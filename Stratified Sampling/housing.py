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
print(strat_test_set["income_cat"].value_counts()/len(strat_test_set))
print(housing_full["income_cat"].value_counts() / len(housing_full))
'''plt.xlabel("income category")
plt.ylabel("number of districts")
plt.show()
print(train_set.shape)
print(test_set.shape)'''

housing = strat_train_set.copy()
#let us create a scatterplot of all the districts to visualize the data
housing.plot(kind="scatter", x="longitude", y="latitude", grid=True, alpha=0.2)#notice how the shape is california
#alpha = controls transparency, darker areas - more overlapping, lighter areas - fewer pts

housing.plot(kind="scatter", x="longitude", y="latitude", grid=True, s=housing["population"]/100,label="population",
             c="median_house_value", cmap="jet", colorbar=True,
             legend=True, sharex=False,figsize=(10,7))
corr_matrix = housing.corr(numeric_only=True)
attributes = ["median_house_value","median_income","total_rooms","housing_median_age"]
scatter_matrix(housing[attributes], figsize=(12,8))
housing.plot(kind="scatter", x="median_income", y="median_house_value", grid=True, alpha=0.2)

#attribute combinations - experiment
housing["rooms_per_house"] = housing["total_rooms"]/housing["households"]
housing["bedrooms_ratio"] = housing["total_bedrooms"]/housing["total_rooms"]
housing["people_per_house"] = housing["population"]/housing["households"]
plt.show()
