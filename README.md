# Wastewater qPCR data

 - Installing using conda:

```
cd wastewater_qpcr_app/
conda env create -f environment.yml
conda activate rapter-env
python wastewater_qpcr_app.py
```

- Using Docker:

```
$ docker run \
    --rm \
    -p 8765:8765 \
    -v "/$PATH:/app/assets/data" \
    poeli/wastewater_qpcr_app:latest
```
