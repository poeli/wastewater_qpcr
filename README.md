# Wastewater qPCR data

 - Installing using conda:

```
cd wastewater_qpcr_app/
conda env create -f environment.yml
conda activate rapter-env
python app.py
```

- Using Docker:

```
$ docker run \
    --rm \
    -p 8765:8765 \
    -v "/{PATH}/wastewater_qpcr.github/data:/app/assets/data" \
    -e "MAXMEM=8000" \
    poeli/wastewater_qpcr_app:latest
```
