from os import error, execl
from flask.globals import request
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import seaborn as sns
import base64
from io import BytesIO
class DataOverview: #path should be here
    def __init__(self,path) -> None:
        self.path = path
        '''Hdf file path here'''
        ext = self.path.split('.')[1]
        if ext == 'h5':
            self.data = pd.read_hdf(path)
        elif ext == 'csv':
            self.data = pd.read_csv(path)
        self.shape = self.data.shape
        self.columns = self.data.columns # remove this later
        self.engine = create_engine('sqlite:///test.db')
        self.cat_var = self.data.select_dtypes(include = 'number').columns
        self.num_var = self.data.select_dtypes(include = 'category').columns

    def csv_to_h5(self):
        hdf_key = 'hdf_key'
        store = pd.HDFStore('hdffile')

        for chunk in pd.read_csv(self.path, chunksize=500000):
            # don't index data columns in each iteration - we'll do it later ...
            store.append(hdf_key, chunk, index=False)
            # index data columns in HDFStore

        store.create_table_index(hdf_key, optlevel=9, kind='full')
        
        store.close()
    def data_to_sql(self): # read in batch and add to sql
        chunksize = 10
        batch = 0
        j =1
        for chunk in pd.read_csv(self.path,chunksize=chunksize):
            df = chunk.rename(columns = {i:i.replace(' ','') for i in chunk.columns})
            df.index +=j
            batch+=1
            df.to_sql('table',if_exists = 'append',con=self.engine)
            j = df.index[-1]+1
        return df
    
    def col_to_sql(self):
        p=0
        batch = 10
        chunksize =10
        total = self.shape[1]
        loops = int(total/chunksize) #loops to perform
        left = total - (loops*chunksize)
        counter = 0
        for _ in range(loops):
            for _ in range(p,batch):
                self.data.iloc[:,counter].to_sql(self.columns[counter],if_exists='append',con=self.engine)
                counter+=1
            p=batch
            batch+=chunksize
        g =0
        while (g<left):
            self.data.iloc[:,counter].to_sql(self.columns[counter],if_exists='append',con=self.engine)
            counter+=1
            g+=1
            
    def data_to_h5(self,path,name):
        df = pd.read_csv(path)
        filename = f'/tmp/{name}.h5' # check if exists
        # hf = h5py.File('data.h5', 'w')
        try:
            df.to_hdf(filename,mode='w',format='table')
            return {'status':True,'message':'Done'}
        except Exception as e:
            return {'status':False,'message':e}
    def read_h5(self,path):
        try:
            df = pd.read_hdf(path,'w') 
            # df = pd.DataFrame(np.array(h5py.File(path)['variable_1']))
            return {'status':True,'message':df}
        except Exception as e:
            return {'status':False,'message':'Error in file reading'}
        
    def stats(self):
        num_stats = self.data.describe(include=['number']).transpose()
        num_stats['kurtosis'] = self.data.kurt(axis=0,numeric_only=True)
        num_stats['skewness']=self.data.skew(axis=0,numeric_only=True)
        num_stats['monotonic']=self.data.apply(lambda k : k.is_monotonic)
        num_stats['95%'] = self.data.quantile(q=0.95)
        num_stats['5%'] = self.data.quantile(q=0.05)
        num_stats['variance'] = self.data.var(numeric_only=True)
        num_stats['missing values'] = self.data.isnull().sum()
        num_stats['missing percent'] = ((self.data.isnull().sum())*self.data.shape[0])/100   
        return num_stats
    
    def filter(self,query):
        try:
            return self.data.query(query)
        except Exception as e:
            return e
    def overview(self):
        cat_stats='No Categorical Data'
        num_stats = self.stats()
        for ty in self.data.dtypes:
            if ty=='object':
                cat_stats = self.data.describe(include=object)
                break

        nvars = self.data.shape[1]
        n_obs= self.data.shape[0]
        mem = self.data.memory_usage(deep=True).sum()
        data_info = {'number of variables':nvars,'number of observations':n_obs,'memory size':mem,'avg mem size':mem/nvars}
        sample = pd.concat([self.data.head(n=5),self.data.tail(n=5)],axis=0)
        return {'sample':sample,'data_info':data_info,'num_stats':num_stats,'cat_stats':cat_stats}


    def overview_variable(self,column_name):
        return self.stats().loc[column_name]


class Graphs(DataOverview):
    def __init__(self,path):
        super().__init__(path)

    def __plot_config(self,**kwargs):
        # plt.figure(figsize=kwargs.get('figsize',(8,8)))
        plt.title(kwargs.get('title',''))
        plt.xlabel(kwargs.get("xlabel",'feature'))
        plt.ylabel(kwargs.get('ylabel','stat'))
        tmpfile = BytesIO()
        plt.savefig(tmpfile, format='png')
        plt.close()
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')    
        
        return encoded
    def missing_data(self):
        plt.figure(figsize=(8,8))
        msng = self.data.isnull().sum()
        msng.plot(kind='bar')
        img = self.__plot_config(title='count',xlabel='features',ylabel='count')
       
        return img

    def hist_plot(self,column_name,**kwargs): # kwargs: hue, y,stat
        '''can have hist,kde,ecef'''
        plt.figure(figsize=kwargs.get('figsize',(8,8)))
        sns.histplot(x=self.data[column_name],bins=10,kde=True)
    
        img = self.__plot_config(title='Histogram',xlabel='features',ylabel='count')
        return img

    def box_plot(self,column_name,**kwargs):# kwargs: hue, y(for grouped by category)
        '''Can have box,count,bar,volin,point,strip,swarm'''
        try:
            plt.figure(figsize=kwargs.get('figsize',(8,8)))
            sns.boxplot(x=self.data[column_name])
            img = self.__plot_config(title='Boxplot',xlabel='features')
            return img
        except TypeError: # might be categorical data
            print('------------yes hererer')
            plt.figure(figsize=kwargs.get('figsize',(8,8)))
            sns.countplot(self.data[column_name])
            img = self.__plot_config(title='countplot',xlabel='features')
            return img

# path = r'C:\Users\Atufa\Projects\ExploratoryDataAnalysis\mydata.csv'
# x = Graphs(path)
# for i in x.columns:
#     x.box_plot(i)

