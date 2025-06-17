import logging
import subprocess
import threading
import os, pty, subprocess, select
import time
import psutil

# ロガーの取得（設定はmain.pyに集約）
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def read_output(master_fd, proc):
    """疑似端末からの出力を読み取る関数"""
    try:
        while True:
            try:
                r, w, e = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    try:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        line = data.decode('utf-8', errors='replace').strip()
                        if line:
                            logger.info(f"[OUTPUT] {line}")
                    except (OSError, IOError) as e:
                        if e.errno == 5:  # Input/output error
                            # プロセスが終了した可能性があるため、終了を確認
                            if proc.poll() is not None:
                                break
                            continue
                        raise
            except select.error:
                # selectエラーが発生した場合、プロセスの状態を確認
                if proc.poll() is not None:
                    break
                continue
    except Exception as e:
        logger.error(f"出力読み取り中にエラーが発生: {e}")
    finally:
        # プロセスが終了していない場合は、残りの出力を読み取る
        try:
            while True:
                try:
                    data = os.read(master_fd, 1024)
                    if not data:
                        break
                    line = data.decode('utf-8', errors='replace').strip()
                    if line:
                        logger.info(f"[OUTPUT] {line}")
                except (OSError, IOError):
                    break
        except Exception:
            pass

def force_kill_process(process, timeout):
    """プロセスを強制的に終了させる関数"""
    logger.info(f"タイムアウト監視を開始します（{timeout}秒）")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            logger.info("プロセスが正常終了しました")
            return
        time.sleep(0.1)
    
    logger.info("タイムアウト発生: プロセスを強制終了します")
    try:
        process.terminate()
        time.sleep(1)
        
        if process.poll() is None:
            logger.info("SIGTERMで終了しないため、SIGKILLを送信します")
            process.kill()
        
        process.wait(timeout=5)
        logger.info("プロセスを強制終了しました")
    except Exception as e:
        logger.error(f"プロセス終了中にエラーが発生: {e}")

def kill_proc_tree(pid):
    """プロセスツリーを強制終了する関数"""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception as e:
        logger.error(f'プロセスツリーkill中にエラー: {e}')

def run_freerouting(dsn_file, output_file=None, version='2.0.1', timeout=15, rules_file="/opt/default.rules", max_passes=250, optimizer_setting="", strategy_setting=""):
    """Freeroutingを実行する関数
    
    Args:
        dsn_file (str): 入力DSNファイル名
        output_file (str, optional): 出力SESファイル名。指定しない場合はDSNファイル名から自動生成
        version (str, optional): Freeroutingのバージョン。デフォルトは'1.9.0'
        timeout (int, optional): タイムアウト時間（秒）。デフォルトは15秒
        rules_file (str, optional): ルールファイル。デフォルトは'/opt/default.rules'
        max_passes (int, optional): 最大パス数。デフォルトは250
        optimizer_setting (str, optional): optimizer設定
        strategy_setting (str, optional): strategy設定
    
    Returns:
        tuple: (成功したかどうか, タイムアウトしたかどうか, 処理時間)
    """
    if output_file is None:
        output_file = os.path.splitext(dsn_file)[0] + ".ses"

    freerouting_jar = f"/opt/freerouting-{version}.jar"

    cmd = [
        "java",
        "-jar",
        freerouting_jar,
        "--gui.enabled=false",
        "-de", 
        dsn_file,
        "-do",
        output_file,
        "-dr",
        rules_file,
        "-mp",
        str(max_passes)
    ]

    if strategy_setting:
        cmd.append("-us")
        cmd.append(strategy_setting)

    if optimizer_setting:
        cmd.append("-oit")
        cmd.append(optimizer_setting)
        
    logger.info(f"cmd {' '.join(cmd)}")

    MAX_RETRY = 4
    RETRY_WAIT = 0.2
    for retry in range(MAX_RETRY):
        start_time = time.time()
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=slave,
                stderr=slave,
                close_fds=True,
                start_new_session=True
            )
            os.close(slave)

            output_thread = threading.Thread(target=read_output, args=(master, proc))
            output_thread.daemon = True
            output_thread.start()

            kill_thread = threading.Thread(target=force_kill_process, args=(proc, timeout))
            kill_thread.daemon = True
            kill_thread.start()

            try:
                proc.wait(timeout=timeout)
                timed_out = False
                elapsed_time = time.time() - start_time
                logger.info(f"プロセスが正常に終了しました（処理時間: {elapsed_time:.2f}秒）")
            except subprocess.TimeoutExpired:
                logger.info("タイムアウト発生: プロセスツリーを強制終了します")
                kill_proc_tree(proc.pid)
                proc.wait()
                timed_out = True
                elapsed_time = time.time() - start_time
                logger.info(f"プロセスが強制終了されました（処理時間: {elapsed_time:.2f}秒）")

            os.close(master)
            logger.info(f"リターンコード: {proc.returncode}")
            logger.info(f"タイムアウト発生: {timed_out}")

            # タイムアウト時はリトライせず即return
            if timed_out:
                return False, True, elapsed_time

            # ファイルサイズチェック
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                logger.info(f"output_file size: {size} (retry {retry+1})")
                if size > 0:
                    return proc.returncode == 0, timed_out, elapsed_time
                else:
                    logger.warning(f"output_file size is 0. リトライします (retry {retry+1})")
                    time.sleep(RETRY_WAIT)
            else:
                logger.warning(f"output_fileが存在しません。リトライします (retry {retry+1})")
                time.sleep(RETRY_WAIT)
        except Exception as e:
            logger.error(f"run_freerouting実行中にエラー: {e}")
            time.sleep(RETRY_WAIT)
        finally:
            try:
                os.close(master)
            except Exception:
                pass
    # すべてのリトライで失敗
    return False, False, 0
