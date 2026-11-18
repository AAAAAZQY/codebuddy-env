import sys
print("python", sys.version.split()[0])
try:
    import pptx
    print("python-pptx", pptx.__version__)
except Exception as e:
    print("no python-pptx:", e)
