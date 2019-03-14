#### Creating zone wise monthly export data for soya and corn
import pandas as pd
import numpy as np
import scipy as sp
from scipy.stats import rv_discrete
from datetime import datetime
from fractions import Fraction
import random
import math
import time
from pandas import DataFrame, merge
import multiprocessing
def allocate_final(year, month, crop, zones,edges,running_capacity,return_final_allocation,unallocated_allocation):
    
    col = ((year-2016)*12) + month + (crop*48)
    zones_export_month = zones.iloc[:,[0,col]]
    zones_export_month = zones_export_month.sort_values(zones_export_month.columns[1], ascending=0)
    
    if(crop == 0):
        product = 'Monthly_Capacity_Soja'
    else:
        product = 'Monthly_Capacity_Milho'

    key = str(year)+'-'+str(month)+'-'+str(crop)
    # return zones_export_month, product

    edges_month = edges[(edges.Year==year) & (edges.Month==month) & (edges.Crop==crop)]  ############

    path_cost = edges_month[edges_month.Leg==1]
    path_cost = edges_month.groupby(['Unique_path_id','Owner'])[['Cost']].sum().reset_index()
    path_cost.columns = ['Path','Owner','Cost']

    zones_paths = edges_month[edges_month.Origin_Type=='zone']
    zones_paths = zones_paths[['Unique_path_id','Origin']]
    zones_paths.columns = ['Path','Zone']

    r_terms_paths = edges_month[edges_month.Origin_Type=='railway terminal']
    r_terms_paths = r_terms_paths[['Unique_path_id','Origin']]
    r_terms_paths.columns = ['Path','Railway Terminal']

    w_terms_paths = edges_month[edges_month.Origin_Type=='water terminal']
    w_terms_paths = w_terms_paths[['Unique_path_id','Origin']]
    w_terms_paths.columns = ['Path','Water Terminal']

    ports_paths = edges_month[edges_month.Destination_Type=='port']
    ports_paths = ports_paths[['Unique_path_id','Destination']]
    ports_paths.columns = ['Path','Port']

    m1 = path_cost.merge(zones_paths,left_on='Path',right_on='Path',how='left')[['Path','Owner','Cost','Zone']]
    m2 = m1.merge(r_terms_paths,left_on='Path',right_on='Path',how='left')[['Path','Owner','Cost','Zone','Railway Terminal']]
    m3 = m2.merge(w_terms_paths,left_on='Path',right_on='Path',how='left')[['Path','Owner','Cost','Zone','Railway Terminal','Water Terminal']]
    allo = m3.merge(ports_paths,left_on='Path',right_on='Path',how='left')[['Path','Owner','Cost','Zone','Railway Terminal','Water Terminal','Port']]

    allo['path'] = allo['Zone'].map(str) +"-" + allo['Railway Terminal'].map(str) + "-" + allo['Water Terminal'].map(str) + "-" +allo['Port'].map(str)

    allo.insert(7, 'Allocation', '0')
    allo.insert(8,'Year',year)
    allo.insert(9,'Month',month)
    allo.insert(10,'Crop',crop)
    allo = allo.sort_values(allo.columns[1], ascending=1)
    # return allo


#### Allocating product to path
   

    
    Allo_final = allo.copy()
    
#     print("calculating step size...")
    exp_colname = zones_export_month.columns[1]
    step = round(sum(zones_export_month[exp_colname])*0.0005,3)
#     print("step size is: ", step)
    
    zones_export_month.reset_index(inplace=True)
    zones_export_month.drop(columns='index',axis=1,inplace=True)
    
    total_export = round(sum(zones_export_month[exp_colname]),3)
#     print(total_export)
    
#     print("calculating probabilites for zone export...")
    export_prob_zone = zones_export_month[exp_colname]/sum(zones_export_month[exp_colname])
    zone_name = zones_export_month.Zone
    zone_number = list(range(len(zones_export_month)))
    
    running_export = zones_export_month.copy()
    
#     print("starting allocation...")
    random.seed(datetime.now())
    i = 0
    rem_export = pd.DataFrame()
    while(total_export > 0 and len(export_prob_zone) > 0 and export_prob_zone.isnull().any().any() == False):
    # while(total_export > 0 and len(export_prob_zone) > 0):
    
        i = i + 1
#         print("\n")
#         print("iteration no: ", i)
        random_variable = rv_discrete(values=(zone_number,export_prob_zone))
        rand_state = str(random_variable.rvs(size=1).tolist()).strip("[]")
    
#         print("Current zone is: ", zone_name[int(rand_state)])
        allo_zone = allo[allo.Zone==zone_name[int(rand_state)]]
        allo_zone.reset_index(inplace=True)
        allo_zone.drop(columns=['index'],axis=1,inplace=True)

        # print("calculating path probabilities...")
        path_id = allo_zone['Path']
        cost_max = round(max(allo_zone['Cost']),3)
        delta = 0.1 * round(min(allo_zone['Cost']),3)
        path_score = (cost_max - allo_zone['Cost'] + delta)
        prob_path = path_score/sum(path_score)
        path_number = list(range(len(allo_zone)))
        random_variable_path = rv_discrete(values=(path_number,prob_path))
        rand_path = str(random_variable_path.rvs(size=1).tolist()).strip("[]")

        export = running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0]
        
        if(export<=0):

            running_export = running_export[running_export.Zone != zone_name[int(rand_state)]]
#             print("Export reaching negative... deleted zone")
            running_export.reset_index(inplace=True, drop= True)
            export_prob_zone = round(running_export[exp_colname]/sum(running_export[exp_colname]),3)
            zone_name = running_export.Zone
            zone_number = list(range(len(running_export['Zone'])))
#             print("Zone Export Probability is: ",export_prob_zone)

            continue 
            
        # print("Fetching path names...")
        railway_terminal = allo['Railway Terminal'][allo.Path == path_id[int(rand_path)]].values[0]
        water_terminal = allo['Water Terminal'][allo.Path == path_id[int(rand_path)]].values[0]
        port = allo['Port'][allo.Path == path_id[int(rand_path)]].values[0]

        # print("Fetching capacities...")
        port_capacity = running_capacity[product][running_capacity.Name == port].values[0]

        if (pd.isnull(water_terminal) == True):
            water_capacity = port_capacity 
        else:
            water_capacity = running_capacity[product][running_capacity.Name == water_terminal].values[0]

        if (pd.isnull(railway_terminal)== True):
             railway_capacity = port_capacity
        else:
             railway_capacity = running_capacity[product][running_capacity.Name == railway_terminal].values[0]

                
        allocation = min((water_capacity,railway_capacity,port_capacity,export,step))
        
        # print("Checking allocation values...")
        if(allocation <= 0 ):
#             print(" **************************** " )
#             print(" $$$$$$$$$$$$$$$$$$$$$$$$$$$$ " )
#             print(" **************************** " )
#             print(" ############################ " )
#             print(" **************************** " )

#             print("Path Capacity full... Deleting path")
            allo = allo[allo.Path != path_id[int(rand_path)]]

            if (len(allo.Path[allo.Zone==zone_name[int(rand_state)]]) == 0):
            



                    unallocated_vol = running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0]
#                     print(unallocated_vol)
                    unallocated_zone = zone_name[int(rand_state)]
                    unallocated_df = pd.DataFrame(index=range(0,1))
                    unallocated_df["Zone"] = unallocated_zone
                    unallocated_df["Volume_Unallocated"] = unallocated_vol
                    unallocated_df["Month"] = month
                    unallocated_df["Year"] = year
                    unallocated_df["Crop"] = crop
#                     print(unallocated_df)
                    rem_export = rem_export.append(unallocated_df,ignore_index= True)
#                     print("rem_df shape : ",rem_export.shape)
#                     print(rem_export)
            #                 print("All Paths Capacity full... Deleting zone")
                    running_export = running_export[running_export.Zone != zone_name[int(rand_state)]]
                    running_export.reset_index(inplace=True, drop= True)

            #                 print("re-calculating Zone probabilities...")
                    export_prob_zone = running_export[exp_colname]/sum(running_export[exp_colname])
                    zone_name = running_export.Zone
                    zone_number = list(range(len(running_export)))
            #                 print("Zone Export Probability is: ",export_prob_zone)
# 
            continue 

#         print("Allocating...")

        Allo_final.Allocation[Allo_final.Path == path_id[int(rand_path)]] = float(Allo_final.Allocation[Allo_final.Path == path_id[int(rand_path)]]) + allocation
        
#         print("Port selected ",port)
        port_value = running_capacity[product][running_capacity.Name == port].values[0]
        # print("Port capacity left before export",port_value)
        
        running_capacity[product][running_capacity.Name == port] = running_capacity[product][running_capacity.Name == port].values[0] - allocation

        if (pd.isnull(water_terminal) == False): 
            running_capacity[product][running_capacity.Name == water_terminal] = running_capacity[product][running_capacity.Name == water_terminal].values[0] - allocation

        if (pd.isnull(railway_terminal)== False):
            running_capacity[product][running_capacity.Name == railway_terminal] = running_capacity[product][running_capacity.Name == railway_terminal].values[0] - allocation
        
        export1 = running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0]
        
        #print("The value of export of rand state before subtracting allocation is",export1)
        
#         print("Port selected ",port)
        port_value = running_capacity[product][running_capacity.Name == port].values[0]
        # print("Port capacity left after export",port_value)
        
        
        running_export.loc[running_export['Zone'] == zone_name[int(rand_state)],"exp_colname"] = round(running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0] - allocation,3)
        
#         print("The value of allocation is",allocation)
        
#         print("The value of export of rand state after subtracting allocation is" , running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0])
        
#         print("The value of allocation in allo final is" , Allo_final.Allocation[Allo_final.Path == path_id[int(rand_path)]])
        
        
        if( running_export[exp_colname][running_export['Zone'] == zone_name[int(rand_state)]].values[0]<=0):
#             print("export values reaching negative... deleting zone")
            running_export = running_export[running_export.Zone != zone_name[int(rand_state)]]
            running_export.reset_index(inplace=True, drop= True)
            
#             print("recalculating zone probabilities...")
            export_prob_zone = running_export[exp_colname]/sum(running_export[exp_colname])
            zone_name = running_export.Zone
            zone_number = list(range(len(running_export['Zone'])))
#             print("Zone Export Probability is: ",export_prob_zone)

        total_export = round(total_export - allocation,3)   
#         print("Total Export Remaining: ",total_export,"\n")
        
        
    # return Allo_final
    export_prob_zone = running_export[exp_colname]/sum(running_export[exp_colname])
    zone_name = running_export.Zone
    zone_number = list(range(len(running_export['Zone'])))
    
    unallocated_allocation[key] = rem_export
    return_final_allocation[key]= Allo_final


def main():
    
    delt_zone = []
    delt_path = []
    
    start_time = time.clock()

    input_file_name = input("Enter Input File Name: ")
    output_file_name = input("Enter Output File Name: ")

    from_year = input("Enter Start Year: ")
    to_year = input("Enter End Year: ")

    from_month = input("Enter Start Month: ")
    to_month = input("Enter End Month: ")

    crop_name = input("For which crop, you want to run the allocation? (soya/corn/both): ")

    if(crop_name.lower() == "soya"):
    	crop_num1 = 0
    	crop_num2 = 1
    elif(crop_name.lower() == "corn"):
    	crop_num1 = 1
    	crop_num2 = 2
    elif(crop_name.lower() == "both"):
    	crop_num1 = 0
    	crop_num2 = 2
    else:
    	print("You have entered wrong input!!! ")
    
    print("Reading Routes Data...")
    edges = pd.read_excel(input_file_name,sheet_name="Paths")

    print("Reading Zonal Information Data...")
    zones = pd.read_excel(input_file_name,sheet_name="Zone_Export")

    print("Reading Terminal Capacity Data...")
    capacity = pd.read_excel(input_file_name,sheet_name="Capacities")
    
    #Resetting Index
    edges.reset_index(inplace=True)
    edges.drop(columns='index',axis=1,inplace=True)
    zones.reset_index(inplace=True)
    zones.drop(columns='index',axis=1,inplace=True)
    capacity.reset_index(inplace=True)
    capacity.drop(columns='index',axis=1,inplace=True)
    
    final_allocation_all = pd.DataFrame()
    rem_df= pd.DataFrame()
    running_capacity = capacity.copy()
    # #for multiprocessing
    manager= multiprocessing.Manager()
    return_final_allocation = manager.dict()
    unallocated_allocation = manager.dict()
    # return_zone_dict = manager.dict()
    # return_product_dict = manager.dict()
    # return_allo_dict = manager.dict()
    # return_Allo_Final_dict =  manager.dict()
    jobs=[]

    for crop in range(crop_num1,crop_num2):
        for year in range(int(from_year),int(to_year) + 1):
            for month in range(int(from_month),int(to_month) + 1):


                key = str(year)+'-'+str(month)+'-'+str(crop)

#                 print("Creating Zone Export Table...")
                # zones_export_month,product = zone_export_table(year, month, crop, zones)
                p = multiprocessing.Process(target=allocate_final, args=(year, month, crop, zones,edges,running_capacity,return_final_allocation,unallocated_allocation))

#                 print("Creating Allocation Table...")
                # allo = allocation_table(year, month, crop, edges)

                # running_capacity = capacity.copy()
                jobs.append(p)
                p.start()

            for proc in jobs:
                proc.join()

                # Allo_Final = Allocate_Export(running_capacity, zones_export_month, allo, product)
                # final_allocation_all = final_allocation_all.append(Allo_Final)

#     print(return_final_allocation)
    for values in return_final_allocation.keys():
        final_allocation_all = final_allocation_all.append(return_final_allocation[values])
    final_allocation_all.to_csv(output_file_name, encoding = 'utf-8-sig', index = False)
    
    for values in unallocated_allocation.keys():
        rem_df = rem_df.append(unallocated_allocation[values])
    rem_df.to_csv("Unallocated_Export.csv", encoding = 'utf-8-sig', index = False)

    print("\n")
    print("Total Execution Time: ",round(time.clock() - start_time,2), "Seconds...")
    print("Total Execution Time: ",round(time.clock() - start_time,2)/60, "Minutes...")
    print("Total Execution Time: ",round(time.clock() - start_time,2)/3600, "Hours...")
    
if __name__ == '__main__':
    
    main()