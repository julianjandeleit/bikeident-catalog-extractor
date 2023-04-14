#%%
import tabula
import pandas as pd
#import pdftotext
#path_pdf = "/home/julian/Downloads/Schwalbe Katalog 2022.pdf"
path_pdf = "C:/Users/Julian/Downloads/Schwalbe Katalog 2022.pdf"
#%%
dfs = tabula.read_pdf(path_pdf,pages=[22,23],pandas_options={"header":None})
len(dfs)
first :pd.DataFrame = dfs[0]
first.to_csv("data/table_out.csv",index=None)
#tabula.convert_into(path_pdf, "output.csv", output_format="csv", pages="all")
# %% Extract raw text (not that useful for us)

#with open(path_pdf, "rb") as f:
#    pdf = pdftotext.PDF(f)
    
#print(len(pdf))

# Iterate over all the pages
#for page in pdf:
#    print(page)

# Read some individual pages
#print(pdf[0])
#print(pdf[1])
#with open("output.txt", "w") as text_file:
#    text_file.write(pdf[22])
# %% 
import camelot.io as camelot
tables = camelot.read_pdf('/home/julian/Downloads/Michelin Katalog 2022.pdf',pages="26", flavor="stream")
#tables = camelot.read_pdf('/home/julian/Downloads/Schwalbe Katalog 2022.pdf',pages="22", flavor="stream")
#tables = camelot.read_pdf('/home/julian/Downloads/drive-download-20230414T201203Z-001/Continental Katalog 2022.pdf',pages="16", flavor="stream")
#tables = camelot.read_pdf('/home/julian/Downloads/drive-download-20230414T201203Z-001/Vittoria Katalog 2022.pdf',pages="13", flavor="stream")
len(tables)