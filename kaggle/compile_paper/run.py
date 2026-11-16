"""Compile the paper draft on Kaggle (no local LaTeX): pdflatex + bibtex from the private paper dataset.

Upload: python kaggle/upload_paper.py ; push: python kaggle/kg.py kernels push -p kaggle/compile_paper
Outputs: main.pdf, main.log, compile.txt in /kaggle/working.
"""
import glob
import os
import shutil
import subprocess

src = os.path.dirname(glob.glob("/kaggle/input/**/main.tex", recursive=True)[0])
work = "/tmp/paper"
shutil.copytree(src, work)
log = open("/kaggle/working/compile.txt", "w")
subprocess.call("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq texlive-latex-base "
                "texlive-latex-recommended texlive-latex-extra texlive-publishers texlive-fonts-recommended "
                "texlive-bibtex-extra > /dev/null", shell=True, stdout=log, stderr=log)
for command in (["pdflatex", "-interaction=nonstopmode", "main.tex"], ["bibtex", "main"],
                ["pdflatex", "-interaction=nonstopmode", "main.tex"], ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
    code = subprocess.call(command, cwd=work, stdout=log, stderr=log)
    log.write(f"\n=== {' '.join(command)} -> {code}\n")
log.close()
for name in ("main.pdf", "main.log", "main.blg"):
    if os.path.exists(os.path.join(work, name)):
        shutil.copy(os.path.join(work, name), "/kaggle/working/")
