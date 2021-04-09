###################################################
#
# README file for bgp.py script.
#
# Please go through this prior script execution  
#
#  
#
####################################################

THE SCRIPT "bgp.py" is written for IOSXR platform. So execute the script on Cisco IOSXR device.

1. Filter used to config are stored in the file 
    bgp_cfg_all_data.txt ==> To configure all configs needed to bring up BGP.
 
    Note: The interface is hardcoded to be Gigabitethernet0/0/0/0 in the query
           and neighbor address is hardcoded to 1.1.1.1
      
          Update the interface in the "bgp_cfg_all_data.txt" according to the interface
           present in your device used to execute the script.

    Query to filter operational data is stored in the file "bgp_neighbor_oper_data.txt"

    Note : Neighbor address is hardcoded to 1.1.1.1 in the query. Update the neighbor address in the 
           file "bgp_neighbor_oper_data.txt" if you want to verify a diffrent IBGP neighbor
     
2. The script is interactive so you can select the options displayed on board when you hit execution.

3. One you select the option, enter the device details the script prompts on which you would like to 
    perform the operation selected in Step 2.

3. Device login will ask for device_ip/hostname, netconf port to interact and username/pwd.
     Key in as prompted by the script.

4. Verification:
       
      1. Configs fetched by get_config will get stored in the file "get_bgp_cfg_<device_ip>.txt"
      2. RPC response obtained from IBGP neighbors operational data will get stored in the file "getoper_ibgp_{host_id}_data.txt"
      3. Capabilities fectched from the device will get stored at "capabilities_rpc_resp_<device_ip>.txt"
