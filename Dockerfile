# Base Image
FROM freesurfer/freesurfer:7.4.1

COPY run_freesurfer.py /run_freesurfer.py
RUN chmod +x /run_freesurfer.py
ENTRYPOINT ["/usr/local/freesurfer/python/bin/python3.8", "/run_freesurfer.py"]