###########################################################################################
# 
#  AUTHOR : Siddesh Nayak
#  
#  Descripttion:
#      This script can be used to collect the operational information
#       of the SDWAN fabric
#
#        1. Dashboard Summary
#        2. Real-time monitoring
#        3. System resource utilization
#        4. Administration or security audits -- Yet to be implemented
# 
# NOTE : The script is interactive and you can key-in options to get desired operations
#        Modify ur stats query in the "stats_query.json" file according to your device information
#
############################################################################################

from sdwan_custom_sdk import SDWAN_SDK
import json
import time
import requests
from datetime import datetime, timezone

def main():

    session=SDWAN_SDK.connect_sdwan_instance_sandbox()

    print("Enter 1 ==> Dashboard summary stats")
    print("Enter 2 ==> Realtime tunnel stats")
    print("Enter 3 ==> Fetching valid query fields")
    print("Enter 4 ==> Fetching system stats queried\n")

    option=int(input("Keyin Option : "))

    if option == 1:
        #### Collecting Dashboard summary
        api_calls=[session.fetch_alarm_count,
                  session.fetch_certificate_summary,
                  session.fetch_control_status]
        SDWAN_SDK.api_calls_exec(api_calls)

    elif option == 2:
        ##### Collecting real-time monitoring stats
        ##### Here we will collect tunnel statistics and performance data
        #####   of all the tunnels connecting to vEgdes
        ### API docs ref
        ## https://developer.cisco.com/docs/sdwan/#!device-realtime-monitoring/users

        resp=session.get_vEdges_info(model="vedge-cloud")
        #print(json.dumps(resp.json()["data"],indent=2))
        vedge_list=resp.json()["data"]
        for vedge in vedge_list:
            if vedge.get("configStatusMessage","") == "In Sync":
                vedge_system_ip=vedge["system-ip"]

                tnl_rtm_stats_resp=session.fetch_device_tunnel_stats_real_time(vedge_system_ip)
                #print(json.dumps(tnl_rtm_stats_resp.json(),indent=2))
                for stats in tnl_rtm_stats_resp.json()["data"]:
                    print (f"Tunnel: {stats['tunnel-protocol']}, src --> dst: {stats['source-ip']} -> {stats['dest-ip']}, Colour : {stats['remote-color']}")
                    print (f"      pkts tx/rx: {stats['tx_pkts']}/{stats['rx_pkts']}")

    elif option == 3:
        ###### Collecting system utilization stats CPU and Mem
        ##### We need to create the query here, where we specify
        #####   the rules where we mention the conditions when we want to collect
        #####   the data and then we specify the components which we want to collect
        ####    the data about like memory or cpu stats

        #### How to determine valid query fields
        ## Doc link : https://developer.cisco.com/docs/sdwan/#!query-format/determine-field-names-and-data-types
        ##
        #

        print("API isnt functional")
        #api_call=[session.get_valid_query_fields_data]
        #SDWAN_SDK.api_calls_exec(api_call)

    elif option ==4:

        ### Collecting Systems stats - Mem and CPU utilization
        ### the column field in the resonse are the valid "field"
        ####  in the query

        with open("stats_query.json","r") as fp:
            query=json.load(fp)

        sys_stats_resp=session.get_system_stats_queried(query)
        #print(json.dumps(sys_stats_resp.json(),indent=2))
        if sys_stats_resp.json()["data"] == []:
            print("System Stats data not available")
        else:
            for stat in sys_stats_resp.json()["data"]:
                dtg = datetime.fromtimestamp(stat["entry_time"] // 1000, timezone.utc)
                cpu = round(stat["cpu_user_new"], 2)
                mem = round(stat["mem_util"], 2)
                print(f"Time:{dtg}, CPU_Util: {cpu}%, mem_util: {mem}%")


if __name__ == "__main__":
    main()