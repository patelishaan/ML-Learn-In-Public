from pathlib import Path
import pandas as pd
import numpy as np
import tarfile
import urllib.request
import matplotlib.pyplot as plt
from zlib import crc32
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit
from pandas.plotting import scatter_matrix
from sklearn.impute import SimpleImputer



pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

def load_housing_data():
    datasets_path = Path("datasets")
    tarball_path = datasets_path / "housing.tgz"
    housing_path = datasets_path / "housing"

    if not housing_path.exists():
        datasets_path.mkdir(parents=True, exist_ok=True)

        if not tarball_path.exists():
            url = "https://github.com/ageron/data/raw/main/housing.tgz"
            urllib.request.urlretrieve(url, tarball_path)

        with tarfile.open(tarball_path) as housing_tarball:
            housing_tarball.extractall(path=datasets_path)

    return pd.read_csv(housing_path / "housing.csv")

def is_id_in_test_set(identifier, test_ratio):
    return crc32(np.int64(identifier))<test_ratio*2**32

def split_data_with_id_hash(data,test_ratio, id_column):
    ids = data[id_column]
    in_test_set = ids.apply(lambda id: is_id_in_test_set(id, test_ratio))
    return data.loc[~in_test_set], data.loc[in_test_set]

housing_full = load_housing_data()
#print(housing_full.head())
#housing_full.hist(bins=50, figsize=(12,8))
#plt.show()
housing_with_id = housing_full.reset_index()
housing_with_id["id"] = (housing_full["longitude"]*1000
                         + housing_full["latitude"])
#train_set, test_set = split_data_with_id_hash(housing_with_id,0.2, "index")
train_set, test_set = train_test_split(housing_full, test_size=0.2, random_state=42)
housing_full["income_cat"] = pd.cut(housing_full["median_income"],
                                    bins = [0,1.5,3.0,4.5,6.,np.inf],
                                    labels=[1,2,3,4,5])
cat_counts = housing_full["income_cat"].value_counts().sort_index()
#cat_counts.plot.bar(rot=0, grid=True)

splitter = StratifiedShuffleSplit(n_splits=10, test_size=0.2, random_state=42)
strat_splits = []
for train_index, test_index in splitter.split(housing_full,
                                              housing_full["income_cat"]):
    strat_train_set_n = housing_full.loc[train_index]
    strat_test_set_n = housing_full.loc[test_index]
    strat_splits.append((strat_train_set_n, strat_test_set_n))
strat_train_set, strat_test_set = train_test_split(housing_full, test_size=0.2, random_state=42, stratify=housing_full["income_cat"])
housing = strat_train_set.copy()

'''housing.plot(kind="scatter", x="longitude", y="latitude", grid=True, s=housing["population"]/100,label="population",
             c="median_house_value", cmap="jet", colorbar=True,
             legend=True, sharex=False,figsize=(10,7))'''
attributes = ["median_house_value","median_income","total_rooms","housing_median_age"]
#scatter_matrix(housing[attributes], figsize=(12,8))
#housing.plot(kind="scatter", x="median_income", y="median_house_value", grid=True, alpha=0.2)

#attribute combinations - experiment
housing["rooms_per_house"] = housing["total_rooms"]/housing["households"]
housing["bedrooms_ratio"] = housing["total_bedrooms"]/housing["total_rooms"]
housing["people_per_house"] = housing["population"]/housing["households"]

corr_matrix = housing.corr(numeric_only=True)
#print(corr_matrix["median_house_value"].sort_values(ascending=False))
#new attribute bedroom ratio is much more correlated with median house value

housing_full=strat_test_set.drop("median_house_value", axis=1)
housing_labels = strat_test_set["median_house_value"].copy()

#1 - CLEANING DATA (MISSING VALUES)
#least destructive - data imputation
'''median = housing["total_bedrooms"].median()
housing["total_bedrooms"] = housing["total_bedrooms"].fillna(median)'''
#using sklearn simple imputer
imputer = SimpleImputer(strategy="median")
housing_num = housing.select_dtypes(include=[np.number])
imputer.fit(housing_num)#calculated the median of each attribute and stored result
print("these are the imputer statistics -",imputer.statistics_)
print("these are actual medians",housing_num.median().values) #as you can see, the values of imputer and actual median matches
X = imputer.transform(housing_num)

housing_tr = pd.DataFrame(X, columns=housing_num.columns,
                          index = housing_num.index)

#handling text and categorical attributes
housing_cat = housing[["ocean_proximity"]]
#print(housing_cat.head(8))
#lets convert this into numbers
#from sklearn.preprocessing import OrdinalEncoder
#ordinal_encoder = OrdinalEncoder()
#housing_cat_encoded = ordinal_encoder.fit_transform(housing_cat)
#print(housing_cat_encoded[:8])
#print(ordinal_encoder.categories_)

from sklearn.preprocessing import OneHotEncoder
cat_encoder = OneHotEncoder()
housing_cat_onehot = cat_encoder.fit_transform(housing_cat)

print(housing_cat_onehot.toarray())

