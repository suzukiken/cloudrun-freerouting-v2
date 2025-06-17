For Local Docker
```
docker build -t freeroutingv2 .
docker run -it --rm freeroutingv2 bash
java -jar freerouting-2.0.1.jar -de /opt/sample.dsn -do /opt/output.ses --gui.enabled=false
java -jar freerouting-2.0.1.jar --gui.enabled=false -de test/pcb.dsn -do test/pcb.ses -dr test/pcb.rules -mp 1000
docker run -it --rm -p 8080:8080 freeroutingv2
```

For GCP CloudRun:
```
docker build . -t freeroutingv2 --platform linux/amd64 && \
docker tag freeroutingv2 asia-northeast1-docker.pkg.dev/firstcloudrun-323509/v2/freeroutingv2:latest && \
gcloud auth configure-docker asia-northeast1-docker.pkg.dev && \
docker push asia-northeast1-docker.pkg.dev/firstcloudrun-323509/v2/freeroutingv2:latest
gcloud run deploy --image asia-northeast1-docker.pkg.dev/firstcloudrun-323509/v2/freeroutingv2:latest --allow-unauthenticated --memory 2Gi --concurrency 1 --timeout=600
gcloud run services update-traffic freeroutingv2 --to-latest
```

