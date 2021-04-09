################################################################################################
#  Author : Siddesh Nayak
#  Date   : 4/09/2021
#
#  Title  : Script to read,create and verify BGP config and operation on Cisco IOSXR device
#
#  Description:
#
#  This script can perform 3 operations:
#
#    a) Can fetch the BGP configurations configured on a device
#    b) Can configure basic BGP IPv4 unicast neighbor on a device
#         with the necessary igp and interface configurations needed
#        to bring up IBGP neighborship
#    c) Can verify the IBGP neighborship status
#
# Note:  The script is interactive and key in the details requested
#         during execution
#         Refer to README.txt file prior execution
##################################################################################################

from ncclient import manager
from collections import defaultdict
from ncclient.operations import RPCError
import xmltodict
import json
import time
#from xml.dom import minidom

class bgp(object):

    def connect_device (self):

        host_login=defaultdict(dict)
        host_login={'host':input("hostname or ip : "),
                    'port':int(input("netconf port no : ")),
                    'username':input("username : "),
                    'password':input("password : "),
                    'device_params': {'name':'iosxr'}
                    }
        print ("\nConnected to the device ....")
        device_handle=manager.connect(**host_login)
            #print(r1_mgr)
        return device_handle,host_login['host']


    def get_capability(self,device_handle,host):

        r1_mgr,host_id=device_handle,host
        with open(f"logs/capabilities_rpc_resp_{host_id}.txt", 'w') as fp:
            xpath_flag=0
            for cap in r1_mgr.server_capabilities:
                if "capability:xpath" in cap:
                    xpath_flag = 1
                fp.write(cap)
                fp.write("\n")

        return xpath_flag


    def get_bgp_cfg(self,device_handle,host):

        print ("Obtaining BGP configs from device")
        r1_mgr,host_id=device_handle,host
        xpath=self.get_capability(r1_mgr,host_id)
        ## Capabilities fetched stored in file "capabilities_rpc_resp_<device_ip>}.txt

        bgp_cfg = """
        <filter>
         <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
           <instance></instance>
          </bgp>
         </filter>"""

        data = r1_mgr.get_config(source='running', filter=bgp_cfg)
        ## BGP configs received stored in file get_bgp_cfg_<device_ip>.txt
        with open(f"logs/get_bgp_cfg_{host_id}.txt", 'w') as fp:
            fp.write(str(data))
        return


    def config_bgp_all(self,device_handle,host):

        print ("Configuring all configs to bring IBGP neighbors UP")
        r1_mgr,host_id=device_handle,host

        xpath=self.get_capability(r1_mgr,host_id)
        ## Capabilities fetched stored in file "capabilities_rpc_resp_<device_ip>}.txt

        with open("bgp_cfg_all_data.txt", 'r') as fp:
            bgp_cfg = fp.read()

        print("##### Locking candidate store #####")
        with r1_mgr.locked("candidate"):
            try:
                r1_mgr.discard_changes()
                data = r1_mgr.edit_config(target='candidate', config=bgp_cfg, default_operation='merge')
                print(data)
                print("##### Success - Candidate store update #####")
            except RPCError as e:
                err_data = e._raw
                print(err_data)
            else:
                r1_mgr.commit()
                print("##### Config Committed #####")

        print("##### Unlocked - Candidate store #####")
        print ("#### Configured Successfully ####")
        return


    def verify_ibgp(self,device_handle):

        print ("\nVerifying IBGP neighbors status")
        r1_mgr,host_id=device_handle,host

        xpath=self.get_capability(r1_mgr,host_id)
        ## Capabilities fetched stored in file "capabilities_rpc_resp_<device_ip>}.txt

        with open("bgp_neighbor_oper_data.txt", 'r') as fp:
            bgp_filter = fp.read()

        if xpath:
            xpath_str = '''bgp/instances/instance/instance-active/default-vrf/neighbors/neighbor[neighbor-address='2.2.2.2']/connection-state'''
            data = r1_mgr.get(filter=('xpath', xpath_str))
        else:
            try:
                data = r1_mgr.get(bgp_filter)
                #print(data)
            except RPCError as e:
                err_data=e._raw
                print(err_data)

        with open(f"logs/getoper_ibgp_{host_id}_data.txt", "w") as fp:
            fp.write(str(data))

        ibgp=xmltodict.parse(data.xml)
        #print(json.dumps(ibgp,indent=2))

        ## Only if RPC returns some oper data
        if not ibgp["rpc-reply"]["data"] is None:
            ibgp_state=ibgp["rpc-reply"]["data"]["bgp"]["instances"]["instance"]["instance-active"]["default-vrf"]["neighbors"]

            if ibgp_state:
                if ibgp_state["neighbor"]["local-as"] == ibgp_state["neighbor"]["remote-as-number"]:
                    print ("Neighborship is IBGP")
                else:
                    print ("Neighborship is BGP")

                if ibgp_state["neighbor"]["connection-state"] == "bgp-st-estab":
                    ibgp_neighbor=ibgp_state["neighbor"]["neighbor-address"]
                    print(f"IBGP neighborship is UP with neighbor {ibgp_neighbor}")
                else:
                    print ("IBGP neighborship is not UP")
        else:
            print ("No data obtained for BGP neighbors")

        return

bgp_obj=bgp()
print("Press 1 -> To get bgp configurations configured on device")
print("Press 2 -> To configure all config to bring up BGP on device")
print("Press 3 -> To verify IBGP neighbor status\n")

option=int(input("Enter the operation you would like to perform 1, 2 or 3 => "))

print("\nKey in the device login details on which operation would be performed ")
device_handle,host=bgp_obj.connect_device()
print ("Success - Device connection....")
if option == 1:
    bgp_obj.get_bgp_cfg(device_handle,host)
elif option == 2:
    bgp_obj.config_bgp_all(device_handle,host)
elif option == 3:
    bgp_obj.verify_ibgp(device_handle)
else:
    print ("Invalid option keyed in - Enter 1 or 2 or 3")



