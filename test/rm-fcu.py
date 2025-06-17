import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IN_FILE = "pcb.dsn"
OUT_FILE = "pcb_rm.dsn"

def parse_dsn(content):
    """DSNファイルをパースする"""
    def parse_sexp(s):
        s = s.strip()
        if not s:
            return None
        if s[0] == '(':
            result = []
            s = s[1:].strip()
            while s and s[0] != ')':
                item, s = parse_sexp(s)
                if item is not None:
                    result.append(item)
                s = s.strip()
            return result, s[1:].strip()
        else:
            match = re.match(r'^([^()\s]+)', s)
            if match:
                return match.group(1), s[match.end():].strip()
            return None, s

    result, _ = parse_sexp(content)
    return result

def remove_fcu_entries(sexp):
    """F.cuに関連するエントリを削除する"""
    if not isinstance(sexp, list):
        return sexp

    result = []
    for item in sexp:
        if isinstance(item, list):
            # F.Cuレイヤー定義をスキップ
            if (len(item) >= 2 and 
                item[0] == 'layer' and 
                item[1] == 'F.Cu'):
                continue
            
            # F.Cuに関連するkeepoutをスキップ
            if (len(item) >= 3 and 
                item[0] == 'keepout' and
                isinstance(item[2], list) and
                len(item[2]) >= 2 and
                item[2][1] == 'F.Cu'):
                continue
            
            # F.Cuに関連するoutlineをスキップ
            if (len(item) >= 2 and 
                item[0] == 'outline' and
                isinstance(item[1], list) and
                len(item[1]) >= 3 and
                item[1][2] == 'F.Cu'):
                continue
            
            # F.Cuに関連するshapeをスキップ
            if (len(item) >= 2 and 
                item[0] == 'shape' and
                isinstance(item[1], list) and
                len(item[1]) >= 2 and
                item[1][1] == 'F.Cu'):
                continue
            
            # 再帰的に処理
            processed = remove_fcu_entries(item)
            if processed:  # 空のリストは追加しない
                result.append(processed)
        else:
            result.append(item)
    
    return result

def dumps(sexp, indent=0):
    """S-expressionを文字列に変換する（KiCadのDSNファイル形式に準拠）"""
    if isinstance(sexp, list):
        if not sexp:
            return "()"
        
        # 最初の要素を取得
        first = sexp[0] if sexp else ""
        
        # 特別な処理が必要なケース
        if first == "path" and len(sexp) > 3:
            # pathの場合は座標を8個ずつで改行
            result = "(" + " ".join(map(str, sexp[:3]))  # path pcb 0
            coords = sexp[3:]
            for i in range(0, len(coords), 8):
                if i == 0:
                    result += "  " + "  ".join(map(str, coords[i:i+8]))
                else:
                    result += "\n" + " " * (indent + 12) + "  ".join(map(str, coords[i:i+8]))
            result += ")"
            return result
        
        # 通常の処理
        result = "("
        for i, item in enumerate(sexp):
            if i == 0:
                result += str(item)
            else:
                if isinstance(item, list):
                    result += "\n" + " " * (indent + 2) + dumps(item, indent + 2)
                else:
                    result += " " + str(item)
        result += ")"
        return result
    else:
        return str(sexp)

def main():
    # DSNファイルを読み込む
    with open(IN_FILE, 'r') as f:
        dsn_content = f.read()

    # S-expressionとしてパース
    sexp = parse_dsn(dsn_content)

    # F.cuに関連するエントリを削除
    modified_sexp = remove_fcu_entries(sexp)

    # 結果を保存
    with open(OUT_FILE, 'w') as f:
        f.write(dumps(modified_sexp))

if __name__ == "__main__":
    main()