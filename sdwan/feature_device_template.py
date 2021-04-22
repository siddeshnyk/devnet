##################################################################################################################
# 
#  AUTHOR : Siddesh Nayak
# 
#  Description:
#
#   This script will create a custom feature template from the existing factory default feature template.
#     Customer feature template created will be encapsulated in the device template.  
#        Then apply the device template to the vsmart.
#
# NOTE :  The requests cannot overwrite existing features, so have to delete manually in the gui the implemented features
#          before re-excuting the script again esle you will see HTTP 400 error
#
#        This script is currently designed just to test device template application through api'script
#         and might not work if there are access restrictions
# 
#
################################################################################################################

import requests
import json
from sdwan_custom_sdk import SDWAN_SDK

def main():

    session = SDWAN_SDK.connect_sdwan_instance_sandbox()
    ##Create device template for vSmart device from factory default feature template
    resp=session.create_fd_device_template_vsmart()
    template_id=resp.json()["templateId"]
    print(f"Device template succesfully created\nDevice Template_id ==> {template_id}")

    print("Applying device template to vsmart devices")
    resp_apply=session.apply_device_template(template_id)
    data = resp_apply.json()["summary"]
    print(f"\nvSmart template attachment status: {data['status']}")
    print(f"Result counts: {data['count']}")
    if data['count']['Failure']:
        print("\n######## Displaying failure reason ###############\n\n")
        print (resp_apply.json()["data"][0]["currentActivity"])



if __name__=="__main__":
    main()