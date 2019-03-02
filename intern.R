#cleaning the global environment
rm(list=ls(all=T))

#checking git
rm(list=ls(all=T))

#setting the working directory
setwd('/Users/venkataanandsingirla/Downloads/Insofe/insofe_intern')
library(dplyr)
library(ggplot2)

#reading the data from .data extension
df= read.table('covtype.data',sep = ',')
df= dplyr::glimpse(df)

#understanding the data
summary(df)
str(df)# number of observations=581012,nunber of variables=55

#checking the NA values
sum(is.na(df))

#checking the target variable proportion
table(df$V55)
prop.table(table(df$V55))#class 1 and 2 has 85.22%
                        #class 3= 6%,class 7=3.5%,class 6=3%,class 5=1.6%,class 4=0.4% very low
hist(df$V55)
ggplot(df,aes(x=V55))+theme_bw()+geom_histogram()
#converting the target variables into factors
df$V55<- as.factor(df$V55)

#standardizing the data
library(vegan)
df_std<- decostand(df[,-55],'range')
df_norm<- decostand(df[,-55],'standardize')

#appending target variable to df_std and df_norm
df_std$V55<- df$V55
df_norm$V55<- df$V55

#checking the range 
summary(df)

#plots

#V1-elevation
plot(tapply(df$V1,df$V55,mean))# 7th class has high avg elvation value.4,3,6 are lowest
plot(density(df$V1))#skewed with left tail
boxplot(df$V1)#outliers

#V2-aspect in degrees azimuth
plot(tapply(df$V2,df$V55,mean))#6th,3rd type has high avg aspect degrees.4,5 has lowest
plot(density(df$V2))#has a differnt ditribution 
boxplot(df$V2)

#V3-slope
plot(tapply(df$V3,df$V55,mean))#3rd,4th type has high avg slope value.2,1 has lowest
plot(density(df$V3))#skewd with right tail
boxplot(df$V3)#outliers

#V4-Horizontal_distance_to_hydrology
plot(tapply(df$V4,df$V55,mean))#7,2,1 are nearer to water horizontally .4,6 are far from water horizontally
plot(density(df$V4))#skewd with right  tail
boxplot(df$V4)#outliers

#V5- Vertical_distance_to_hydrology
plot(tapply(df$V5,df$V55,mean))#7,6 are nearer to water in vertical direction.4,6 are far from water in vertical direction
plot(density(df$V5))#skewd with right  tail
boxplot(df$V5)#outliers

#V6- horizontal_distance to roadways
plot(tapply(df$V6,df$V55,mean))#7,2,1 are nearer to road horizontally .4,6,3 are far from road horizontally
plot(density(df$V6))#skewd with right tail
boxplot(df$V6)#outliers

#V7-Hillshade_9am (0 to 255 index)
plot(tapply(df$V7,df$V55,mean))#4th,5th type has high avg hill_shade_index_9am value.3,6 has lowest
plot(density(df$V7))#skewd with left tail
boxplot(df$V7)#outliers

#V8-Hillshade_Noon (0 to 255 index)
plot(tapply(df$V8,df$V55,mean))#1,2 type has high avg hill_shade_index_noon value.6 has lowest
plot(density(df$V8))#skewd with left tail
boxplot(df$V8)#outliers

#V9-Hillshade_3pm (0 to 255 index)
plot(tapply(df$V9,df$V55,mean))#7,1,2 type has high avg hill_shade_index_3pm value.4 has lowest
plot(density(df$V9))#skewd with left tail
boxplot(df$V9)#outliers

#V10-Horizontal_Distance_To_Fire_Points
plot(tapply(df$V10,df$V55,mean))#7,2,1 are nearer to fire_points horizontally .4,6,3 are far from fire_points horizontally
plot(density(df$V10))#skewd with right tail
boxplot(df$V10)#outliers

#checking correlation between numerical atrributes
library(corrplot)
corrplot(cor(df[,1:10]),method = 'number')

#dividing the data train,test
library(caret)
train_idx<- createDataPartition(df_std$V55,p = 0.8,list = F)
train_data<- df_std[train_idx,]
test_data<- df_norm[-train_idx,]

#creating a validation set to check the accuracy
train_id<- createDataPartition(train_data$V55,p=0.9,list=F)
train_set<- train_data[train_id,]
validation<- train_data[-train_id,]


################ models rpart  #######
library(rpart)
rpart_models<- rpart(train_set$V55~.,data = train_set)

#predicting on train data
rpart_tpred<- predict(rpart_models,train_set[,-55],type = 'class');
summary(rpart_tpred)
acc= mean(rpart_tpred==train_set[,'V55']);acc

#predicting on validation
rpart_vpred<- predict(rpart_models,train_set[,-55],type = 'class');rpart_vpred
mean(rpart_vpred==validation[,'V55'])
table(rpart_vpred)
#random forest
library(randomForest)
rf_model<- randomForest(x=train_set[,-55],y=train_set$V55,xtest = validation[,-55],ytest = validation$V55,ntree = 2000,mtry =7 )
rf_model
#predicting on train data
rf_tpred<- predict(rf_model,train_set[,-55])
summary(rf_tpred)
acc= mean(rf_tpred==train_set[,'V55']);acc

#predicting on validation
rf_vpred<- predict(rf_model,train_set[,-55],type = 'class');rf_vpred
mean(rf_vpred==validation[,'V55'])

#