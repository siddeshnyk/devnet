####################################################################################################
#  Author : Siddesh Nayak
#  Date   : 
#
#  Title  : This script collects all the device info in the SD-WAN inventory
#            There are 3 api eexecuted and information is collected tin the file which gives : 
#               1) All devices info
#               2) Only controllers specific info
#               3))Only vEdges specific info
#         
###################################################################################################


import requests
import json
from sdwan_custom_sdk import SDWAN_SDK

def main():

    session=SDWAN_SDK.connect_sdwan_instance_sandbox()
    print(session)

    api_calls=[session.get_device_info_all,
               session.get_controllers_info,
               session.get_vEdges_info]
               
    SDWAN_SDK.api_calls_exec(api_calls)

if __name__ == "__main__":
    main()
