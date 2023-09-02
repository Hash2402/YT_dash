#Librabries
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime 

#Function definitions 
def style_negative(v,props=''):
    #Negative values 
    try:
        return props if v<0 else None
    except:
        pass
def style_positive(v,props=''):
    #Negative values 
    try:
        return props if v>0 else None
    except:
        pass

def great_check(n1,n2):
    if n1<=n2:
        return n1,n2
    else: return n2,n1 
def audience_sample(country):
    if country=="US":
        return 'USA'
    elif country=='IN':
        return 'India'
    else:
        return 'Other'
#get data
#https://youtu.be/Yk-unX4KnV4?si=40PfILf11GHB_dbP
@st.cache_data  
def load_data():
    df_agg=pd.read_csv("Datasets\YT Data\Aggregated_Metrics_By_Video.csv").iloc[1:,:]
    df_agg.columns = ['Video','Video title','Video publish time','Comments added','Shares','Dislikes','Likes',
                        'Subscribers lost','Subscribers gained','RPM(USD)','CPM(USD)','Average % viewed','Average view duration',
                        'Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)','Impressions','Impressions ctr(%)']
    df_agg['Video publish time'] = pd.to_datetime(df_agg['Video publish time'])
    df_agg['Average view duration'] = df_agg['Average view duration'].apply(lambda x: datetime.strptime(x,'%H:%M:%S'))
    df_agg['Avg_duration_sec'] = df_agg['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)
    df_agg['Engagement_ratio'] =  (df_agg['Comments added'] + df_agg['Shares'] +df_agg['Dislikes'] + df_agg['Likes']) /df_agg.Views
    df_agg['Views / sub gained'] = df_agg['Views'] / df_agg['Subscribers gained']
    df_agg.sort_values('Video publish time', ascending = False, inplace = True)  
    df_agg_sub=pd.read_csv("A:\ML\Datasets\YT Data\Aggregated_Metrics_By_Country_And_Subscriber_Status.csv")
    df_comments=pd.read_csv("Datasets\YT Data\All_Comments_Final.csv")
    df_time=pd.read_csv("Datasets\YT Data\Video_Performance_Over_Time.csv")
    df_time['Date']=pd.to_datetime(df_time['Date'])
    return df_agg,df_agg_sub,df_comments,df_time

#get data frames from load_data function
df_agg,df_agg_sub,df_comments,df_time=load_data()
#data engineer

df_agg_diff=df_agg.copy()
#get a 12 month time window
metric_date_12mo=df_agg_diff['Video publish time'].max()-pd.DateOffset(months=12)
median_agg=df_agg_diff[df_agg_diff['Video publish time']>=metric_date_12mo].median()

df_time_diff = pd.merge(df_time, df_agg.loc[:,['Video','Video publish time']], left_on ='External Video ID', right_on = 'Video')
df_time_diff['days_published'] = (df_time_diff['Date'] - df_time_diff['Video publish time']).dt.days

num_cols=np.array((df_agg_diff.dtypes=='float64')|(df_agg_diff.dtypes=='int64'))
df_agg_diff.iloc[:,num_cols]=(df_agg_diff.iloc[:,num_cols]-median_agg).div(median_agg)


date_12mo = df_agg['Video publish time'].max() - pd.DateOffset(months =12)
df_time_diff_yr = df_time_diff[df_time_diff['Video publish time'] >= date_12mo]

views_days = pd.pivot_table(df_time_diff_yr,index= 'days_published',values ='Views', aggfunc = [np.mean,np.median,lambda x: np.percentile(x, 80),lambda x: np.percentile(x, 20)]).reset_index()
views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
views_days = views_days[views_days['days_published'].between(0,30)]
views_cumulative = views_days.loc[:,['days_published','median_views','80pct_views','20pct_views']] 
views_cumulative.loc[:,['median_views','80pct_views','20pct_views']] = views_cumulative.loc[:,['median_views','80pct_views','20pct_views']].cumsum()

#Dashboard
# st.markdown("""
# <style>
# div[data-testid="metric-container"] {

#    background-color: rgba(28, 131, 225, 0.1);
#    border: 1px solid rgba(28, 131, 225, 0.1);
#    paorder-radius: 6px;
#    color: rgb(30, 103, 119);
#    overflow-wrap: break-word;
   
# }

# /* breakline for metric text         */
# div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
#    overflow-wrap: break-word;
#    white-space: break-spaces;
#    color: 9ECB42;
   
# }
# </style>
# """dding: 5% 5% 5% 10%;
#    b
# , unsafe_allow_html=True)
st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 36px;
}
</style>
""",
    unsafe_allow_html=True,
)

add_sidebar=st.sidebar.select_slider('Slide',('Aggregate Metrics','Individual video'))

st.header(":blue[Youtube] :red[Channel] Analysis :bar_chart:")

if add_sidebar=='Aggregate Metrics':
    
    st.warning('Aggregated analysis of the channel')
    df_agg_metrics = df_agg[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    metric_date_6mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =6)
    metric_date_12mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =12)
    metric_medians6mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_6mo].median()
    metric_medians12mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_12mo].median()

    col1,col2,col3,col4,col5=st.columns(5)
    columns=[col1,col2,col3,col4,col5]

    count=0
    for i in metric_medians6mo.index:
        with columns[count]:
            delta=((metric_medians6mo[i]-metric_medians12mo[i])/metric_medians12mo[i])*100
            st.metric(label=i,value=round(metric_medians6mo[i],1),delta="{:.2f}%".format(delta))
            count=count+1
            if count>=5:
                count=0

    #st.metric('Views',metric_medians6mo['Views'],500)
    df_agg_diff['Publish_date'] = df_agg_diff['Video publish time'].apply(lambda x: x.date())
    df_agg_diff_final = df_agg_diff.loc[:,['Video title','Publish_date','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    df_agg_numeric_lst = df_agg_diff_final.median().index.tolist()
    df_to_pct = {}
    for i in df_agg_numeric_lst:
        df_to_pct[i] = '{:.1%}'.format


    st.dataframe(df_agg_diff_final.style.hide().applymap(style_negative,props='color:Orange;').applymap(style_positive,props='color:#00FFFF;').format(df_to_pct))
    #Pie chart 
    fig5=px.line(y=df_agg_diff['Views / sub gained'],x=df_agg_diff['Video title'],title="Video and Subcriber gained in percent ")
    st.plotly_chart(fig5)

    fig7=px.histogram(df_agg_diff_final,x="Avg_duration_sec",y='Engagement_ratio',color='Video title')
    st.plotly_chart(fig7)

if add_sidebar=='Individual video':
    #st.write('Ind')
    
    st.success("Individual video attribute visualization")
    videos=tuple(df_agg['Video title'])
    
    video_select=st.selectbox('Choose a video:',videos)
    agg_filtered = df_agg[df_agg['Video title'] == video_select]
    agg_sub_filtered = df_agg_sub[df_agg_sub['Video Title'] == video_select]
    agg_sub_filtered['Country'] = agg_sub_filtered['Country Code'].apply(audience_sample)
    agg_sub_filtered.sort_values('Is Subscribed', inplace= True)  
    fig=px.bar(agg_sub_filtered,x='Views',y='Is Subscribed',color='Country')
#     fig.update_layout(
#     paper_bgcolor="rgba(28, 131, 225, 0.1)",
# )
    
    st.plotly_chart(fig)

    agg_time_filtered = df_time_diff[df_time_diff['Video Title'] == video_select]
    first_30 = agg_time_filtered[agg_time_filtered['days_published'].between(0,30)]
    first_30 = first_30.sort_values('days_published')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['20pct_views'],
                    mode='lines',
                    name='20th percentile', line=dict(color='purple', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['median_views'],
                        mode='lines',
                        name='50th percentile', line=dict(color='black', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['80pct_views'],
                        mode='lines', 
                        name='80th percentile', line=dict(color='royalblue', dash ='dash')))
    fig2.add_trace(go.Scatter(x=first_30['days_published'], y=first_30['Views'].cumsum(),
                        mode='lines', 
                        name='Current Video' ,line=dict(color='firebrick',width=8)))
        
    fig2.update_layout(title='View comparison first 30 days',
                   xaxis_title='Days Since Published',
                   yaxis_title='Cumulative views')
    
    st.plotly_chart(fig2)
    st.warning("Average Time for videos in last 12 months")
    fig3=px.bar(df_time_diff_yr,y="Video Title",x="Average Watch Time")
    st.plotly_chart(fig3)

    fig4=px.histogram(df_time_diff_yr,x='Video Length',y='Views',title="Video length (In minutes) impact on number of views")
    st.plotly_chart(fig4)
    
    df_temp=df_time_diff_yr
    df_temp['Video Length']=df_temp['Video Length'].fillna(0)
    #st.write(type(df_temp['Views'].iloc[0]))
    pd.to_numeric(df_temp['Video Length'])
    #st.write(type(df_temp['Views'].iloc[0]))
    
    #st.write("Here")
    #st.write("1",len(df_temp),"2",len(df_view_100))

    #define a slider for getting range
    
    def range_select():
        Select_opt1=st.select_slider("Select a range",('0','500','1000','2000','3000'),key="s1")
        
        Select_opt2=st.select_slider("Select a range",('0','500','1000','2000','3000'))
        st.write("Range is ",Select_opt1,"-",Select_opt2)
        if int(Select_opt1)>0 or int(Select_opt2)>0:

            mask1=df_temp['Video Length']>=int(Select_opt1)
            mask2=df_temp[mask1]<=int(Select_opt2)
            df_view_100=df_temp[mask2]
            fig4=px.histogram(df_view_100,x='Video Length',y='Views',title="Video length (In minutes) impact on number of views",color=df_view_100['Video Title'])
            return st.plotly_chart(fig4)
        
            #return st.write("Invalid Range")
    st.button("Range defined chart",help="Click here to manually set range of the above chart")
    Select_opt1=st.select_slider("Select a range",('0','500','1000','1500','2000','2500','3000'),key="s1")
    
    Select_opt2=st.select_slider("Select a range",('0','500','1000','1500','2000','2500','3000'))
    
    if int(Select_opt1)>0 or int(Select_opt2)>0:
        Low,High=great_check(int(Select_opt1),int(Select_opt2))
        
        mask1=df_temp['Video Length']>=float(Low)
        st.success(f"Range is {Low}   to  {High}")
        
        
        df_view_100=df_temp[mask1]
        df_view_100=df_view_100.loc[df_view_100['Video Length']<=float(High)]
        fig4=px.histogram(df_view_100,x='Video Length',y='Views',title=f"Video length (In minutes) impact on number of views in range:- {Low} to {High}",color=df_view_100['Video Title'])
        st.plotly_chart(fig4)
    fig6=px.pie(df_agg_sub,values="Views",names="Country Code",title="Country and Views")
    st.plotly_chart(fig6)
    