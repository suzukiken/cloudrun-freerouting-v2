For Local Docker
```
docker build -t freeroutingv2 .
docker run -it --rm freeroutingv2 bash
java -jar freerouting-2.0.1.jar -de /opt/sample.dsn -do /opt/output.ses --gui.enabled=false
```

For Local jar
```
java -jar freerouting-2.0.1.jar --gui.enabled=false -de test/pcb.dsn -do test/pcb.ses -dr test/pcb.rules -mp 1000
```

```
docker run -it --rm -p 8080:8080 freeroutingv2
```

For GCP CloudRun:
```
gcloud config set project firstcloudrun-323509
gcloud builds submit --tag gcr.io/firstcloudrun-323509/freeroutingv2
gcloud run deploy --image gcr.io/firstcloudrun-323509/freeroutingv2 --platform managed
```

Change timeout setting

```
gcloud run services update freeroutingv2 --timeout=900
```

URL
----
2021.09.09
https://freeroutingv2-3f7bj6d5qa-an.a.run.app