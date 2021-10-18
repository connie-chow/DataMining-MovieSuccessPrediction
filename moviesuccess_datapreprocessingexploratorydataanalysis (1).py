# -*- coding: utf-8 -*-
"""MovieSuccess_DataPreprocessingExploratoryDataAnalysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XrsSaJQ5jfe2DVzpHPbEPmbr63q1iEo7

Project Name: Movie Success Prediction Project

This section includes data collection, dadta preprocessing and exploratory data analysis

Load and merge datasets 
tmdb_5000_movies.csv
all_movie.csv merged into
OMdb_mojo_clean.csv - used for exploratory data analysis
"""

!pip install dython
!pip install cpi

import pandas as pd
import numpy as np
import cpi

from sklearn.preprocessing import OneHotEncoder
from functools import partial
from sklearn.feature_selection import SelectKBest, mutual_info_classif
import statsmodels.api as sm
import matplotlib.pyplot as plt
from dython import nominal

import io


from google.colab import files
uploaded = files.upload()

OMdb = pd.read_csv('OMdb_mojo_clean.csv', na_values = ['NaN', 'inf'])

tmdb = pd.read_csv('tmdb_5000_movies.csv', na_values = ['NaN', 'inf'])

all_movie = pd.read_csv('all_movie.csv', na_values = ['NaN', 'inf'])

"""From all_movie.csv, merge Writer1 through Writer4 into OMdb_mojo_clean.csv
for matching movies by “Title” in all_movie.csv
"""

movie_writers = all_movie.loc[:, (all_movie.columns.str.startswith('Write')) | (all_movie.columns == 'Title')]

OMdb = OMdb.merge(movie_writers, how = 'left', left_on = 'Title', right_on = 'Title')

OMdb.shape

"""From tmdb_5000_movies.csv merge “budget” field into OMdb_mojo_clean.csv by
matching movie “title”
"""

tmdb_new = tmdb[['title', 'budget']]

OMdb = OMdb.merge(tmdb_new, how = 'left', left_on = 'Title', right_on = 'title')

OMdb.drop(columns = ['title'], inplace = True)

"""From Cast1 to Cast 6 all_movie.csv merge into OMdb_mojo_clean.csv by
matching “Title”
"""

movie_casts = all_movie.loc[:, (all_movie.columns.str.startswith('Cast')) | (all_movie.columns == 'Title')]

OMdb = OMdb.merge(movie_casts, how = 'left', left_on = 'Title', right_on = 'Title')

OMdb.shape

OMdb = OMdb.drop_duplicates(keep ='first')

OMdb[OMdb['Title'] == 'The Jungle Book']

def inflate_column(data, column): 
    return data.apply(lambda x:cpi.inflate(x[column], x.Year), axis = 1)

OMdb['real_budget'] = inflate_column(OMdb, 'budget')
OMdb['real_revenue'] = inflate_column(OMdb, 'worldwide-gross')

"""### Data Preprocessing

In OMdb_mojo.clean.csv, clean up the “nan” and “inf” and set them to 0
"""

OMdb._get_numeric_data().isnull().sum().sort_values(ascending = False).head(10)

OMdb.loc[OMdb['BoxOffice'].isnull(), 'BoxOffice'] = 0

OMdb.loc[OMdb['logBoxOffice'].isnull(), 'logBoxOffice'] = 0

OMdb.loc[OMdb['budget'].isnull(), 'budget'] = 0

OMdb.loc[OMdb['overseas-gross'].isnull(), 'overseas-gross'] = 0

OMdb.loc[OMdb['bo_year_rank'].isnull(), 'bo_year_rank'] = 0

OMdb.loc[OMdb['domestic-gross'].isnull(), 'domestic-gross'] = 0

OMdb._get_numeric_data().isnull().sum().sort_values(ascending = False).head(10)

OMdb = OMdb.fillna('0')

OMdb.isnull().sum()

"""Drop all records in OMdb_mojo_clean.csv that have budget = 0 or empty OR if
revenue = 0 or empty
"""

OMdb = OMdb[(OMdb[['budget', 'worldwide-gross']] != 0).all(axis =1)]

OMdb.shape

OMdb.to_csv('OMdb_merged.csv', index = False)
from google.colab import files
files.download("OMdb_merged.csv")

"""Perform hot encoding for all the non-numeric data columns in OMdb_mojo_clean.csv,
need to have the data ready to be fed to sci-kit library calls for logistic regression, KNN, SVM etc.
"""

cat_cols = np.array(pd.DataFrame(OMdb.dtypes[OMdb.dtypes == 'object']).index)

ohe = OneHotEncoder(drop = 'first')

ohe_array = ohe.fit_transform(OMdb[cat_cols]).toarray()

ohe_OMdb = pd.DataFrame(ohe_array, index = OMdb.index, columns = ohe.get_feature_names())

ohe_OMdb.head()

OMdb_drop_col = OMdb.drop(columns = cat_cols)

OMdb_ohed = pd.concat([OMdb_drop_col, ohe_OMdb], axis = 1)

OMdb_ohed.head()

OMdb_ohed.to_csv('OMdb_ohed.csv', index = False)

"""correlation matrix using features which are guessed to have impact on the box office sales: Awards, Director, Genre, IMdb_score, Production, Rated, Writer 4, Writer 3, Runtime, actor_1, actor_2, worldwide-gross, studios, oscar_noms, oscar_wins, writer2, overseas-gross, awards, director_1, director_2, imdb_votes, nomination, writer1, language"""

corr_df = OMdb[['Awards', 'Runtime','IMdb_score', 'worldwide-gross', 'director_2', 'Production', 'studio',
               'imdbVotes','Rated', 'oscar_noms', 'nominations','Writer 4', 'oscar_wins', 'Writer 1',
               'Writer 3', 'Writer 2', 'Language']]

nominal.associations(corr_df, nominal_columns = 'all', figsize=(15, 15), annot =True)

"""Covariance matrix to determine which features are similar and can be dropped from model input"""

OMdb.cov()

"""### Exploratory Data Analysis
Plot some graphs using OMdb_mojo_clean.csv to explore relationship between certain features and box office sales

Plot revenue by genre. Revenue comes from “worldwide-gross” and “Genre” in OMDb_mojo_clean.csv
"""

OMdb['genre_1'] = [i.split(',')[0] for i in OMdb['Genre'] ]

genre_revenue_df= pd.DataFrame(OMdb.groupby(['genre_1']).sum()['real_revenue'])

genre_revenue_df

plt.figure(figsize = (10, 5))
plt.bar(genre_revenue_df.index, genre_revenue_df['real_revenue'])
plt.title('Real Revenue By Genre')
plt.xlabel('Genre')
plt.ylabel('Real Revenue \n (in 100 Billions)')
plt.savefig('Real Revenue By Genre.png');

"""Bin movies by the month that they are released.  Shows which months of the year generate the highest box office sales on average."""

month = []
for data in OMdb['Released']:
    if data != '0':
        month.append(pd.to_datetime(data).month)
    else:
        month.append(0)
        
OMdb['month'] = month

OMdb['month'].value_counts()

month_revenue_df =pd.DataFrame(OMdb.groupby(by = ['month', 'Title']).sum()['real_revenue'])

month_revenue_df.reset_index(inplace = True)

plt.scatter(month_revenue_df['month'], month_revenue_df['real_revenue'])
plt.title('Real Revernue Generated \n per Movie per Month')
plt.xlabel('Month')
plt.ylabel('Real Revenue \n (in Billions)')
plt.savefig('Real Revernue Generated per Movie per Month.png');

"""Calculate the percentage return on a movie and bin them by director.  Shows which directors have highest return, is there any correlation to box office sales?"""

OMdb['pct_return'] = OMdb['real_budget']/OMdb['real_revenue']*100

OMdb.columns

OMdb['pct_return'] = OMdb['pct_return'].astype(float)

OMdb['pct_return'].dtype

revenue_director_df = pd.DataFrame(OMdb.groupby(by=['Director']).mean()['pct_return']).sort_values(by = 'pct_return', ascending = False)

revenue_director_df = revenue_director_df.sort_values(by = 'pct_return')

plt.figure(figsize = (50,50))
plt.barh(revenue_director_df.index, revenue_director_df['pct_return'])
plt.title('Percentage Return \n on Average per Director', fontsize = 40)
plt.xlim(0,800)
plt.xlabel('Percentage Return', fontsize = 30)
plt.ylabel('Director', fontsize = 30)
plt.savefig('Percentage Return on Average per Director.png');

"""Scatter plots of relationship of worldwide-gross to various features such as studio, oscar wins, oscar nomination, total number of awards won, actor_1 and writer_1"""

# Worldwide-gross to production studio
wwg_production_df = pd.DataFrame(OMdb.groupby(by=['Production']).sum()['real_revenue']).sort_values(by='real_revenue', ascending = False)
plt.figure(figsize = (35,7))
wwg_studio_df = pd.DataFrame(OMdb.groupby(by=['studio']).sum()['real_revenue']).sort_values(by='real_revenue', ascending = False)
plt.figure(figsize = (35,7))

plt.figure(figsize = (30,15))
ax1 = plt.subplot(2,1,1)
ax1.set_title('Revenue by Production', fontsize = 30)
ax1.bar(wwg_production_df.index, wwg_production_df['real_revenue'])
ax1.set_xlabel('Production', fontsize = 15)
ax1.set_xticklabels(wwg_production_df.index, rotation = 90)
ax1.set_ylabel('Real Revenue \n (in 10 Billions)', fontsize = 15)

ax2 = plt.subplot(2,1,2)
ax2.set_title('Revenue by Studio', fontsize = 30)
ax2.bar(wwg_studio_df.index, wwg_studio_df['real_revenue'])
plt.figure(figsize = (35,7))
ax2.set_xlabel('Studio', fontsize = 15)
ax2.set_xticklabels(wwg_studio_df.index, rotation = 90)
ax2.set_ylabel('Real Revenue \n (in 10 Billions)', fontsize = 15)

plt.tight_layout()
plt.savefig('Real Revenue to production studio.png');

# Worldwide-gross to # of oscar wins
plt.scatter(OMdb['oscar_wins'], OMdb['real_revenue'])
plt.title('Real Revenue to number of Oscar wins')
plt.xlabel('Number of Oscar Wins')
plt.ylabel('Real Revenue \n (in Billions)')
plt.savefig('Real Revenue to number of Oscar wins.png');

# Worldwide-gross to # of oscar nominations
plt.scatter(OMdb['oscar_noms'], OMdb['real_revenue'])
plt.title('Real Revenue to Number of Oscar Nominations')
plt.xlabel('Number of Oscar Nomination')
plt.ylabel('Real Revenue \n (in Billions)')
plt.savefig('Real Revenue to number of Oscar nominations.png');

#Worldwide-gross to total # awards won
plt.scatter(OMdb['awards'], OMdb['real_revenue'])
plt.title('Real Revenue to Total Number of Award Won')
plt.xlabel('Number of awards')
plt.ylabel('Real Revenue \n (in Billions)')
plt.savefig('Real Revenue to Total Number of Award Won.png');

# Try using log to see if any linear relationship?
plt.scatter(np.log(OMdb['awards']), np.log(OMdb['real_revenue']))
plt.title('Real Revenue to \n Number of Award Wins After Logarithm')
plt.xlabel('Natural Log of the Number of awards')
plt.ylabel('Natural Log of the Real Revenue')
plt.savefig('Real Revenue to Number of Award Wins After Logarithm.png');

# Worldwide-gross to actor_1
wwg_actor1_df = pd.DataFrame(OMdb.groupby(by=['actor_1']).sum()['real_revenue']).sort_values(by='real_revenue')
plt.figure(figsize = (40,45))
plt.barh(wwg_actor1_df.index, wwg_actor1_df['real_revenue'])
plt.title('Real Revenue by actor_1', fontsize = 40)
plt.xlabel('Real Revenue \n (in 10 Billions)', fontsize = 30)
plt.ylabel('Actor Name', fontsize = 30)
plt.savefig('Real Revenue by actor_1.png');

# Worldwide-gross to writer_1
wwg_writer_df = pd.DataFrame(OMdb.groupby(by=['Writer 1']).sum()['real_revenue']).sort_values(by='real_revenue')
plt.figure(figsize = (40,45))
plt.barh(wwg_writer_df.index, wwg_writer_df['real_revenue'])
plt.title('Real Revenue by Writer_1', fontsize = 40)
plt.xlabel('Real Revenue \n (in 10 Billions)', fontsize = 30)
plt.ylabel('Writer Name', fontsize = 30)
plt.savefig('Real Revenue by Writer_1.png');

