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
