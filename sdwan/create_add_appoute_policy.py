#########################################################################################
# 
#  AUTHOR : Siddesh Nayak
# 
#  Description:
#
#   This script will create an app-route policy on vSmart and attach the policy to the sites
#    part of the vpn
#
#   Policy definition : To match voice traffic DSCP EF, and use transport as mpls
#                         if the mpls transport meets the sla criteria
#
#   Policy application site : Apply the policy on the sites belonging to the vpn
#
#
#
############################################################################################

import json
from sdwan_custom_sdk import SDWAN_SDK

def main():

    ###############################################################################
    ## 
    ##  We need to create 3 policy objects required to create the policy
    ##   1) site_object
    ##   2)vpn_object
    ##   3) sla_object
    ##
    ## Next we need to create the mesh topology by tieing the sites to the vpn
    ## Once we have the topology we need to create the app_route policy
    ##   utilizing the 3 policy  objects we created.
    ## Then we need to apply the policy to the sites part of that vpn.
    ##
    #################################################################################

    session=SDWAN_SDK.connect_sdwan_instance_sandbox()
    #site_name=input("Enter name for the site : ")
    #region_of_site=input("Enter name of region which site belongs to : ")
    site_id_list=[{"siteId":"1001"},{"siteId":"1002"}]
    vpn_id="1"
    vpn_list=[{"vpn":vpn_id}]
    #vpn_name = input("Enter name for the vpn : ")
    sla=[{"latency":"150","jitter":"1","loss" : "30"}]
    topology_name="NCE_mesh"

    #approute_policy_name=input("Enter name for approute policy to be created : ")
    description = "MPLS preferred transport for VOICE over Internet"
    dscp_value="46"
    primary_link_pref="mpls"
    alternate_link_pref = "biz-internet"
    site_name, region_of_site, vpn_name, approute_policy_name = "Cisco_Site_NJ", "Eastcoast_Region", "NCE_VPN", "VOIP_MPLS"

    type1,type2,type3 = "site","vpn","sla"
    resp_site=session.create_site(site_name,type1,site_id_list)
    resp_vpn=session.create_vpn(vpn_name,type2,vpn_list)
    resp_sla=session.define_sla("customVoiceSLa",type3,sla)

    site_obj_id=resp_site.json()["listId"]
    vpn_obj_id=resp_vpn.json()["listId"]
    sla_obj_id=resp_sla.json()["listId"]
        
    region_list=[{"name": region_of_site,"siteLists": [site_obj_id]}]
    resp_topo=session.create_topology(topology_name,vpnObjectId=vpn_obj_id,region_site_list=region_list)
    resp_approute=session.create_approute_policy(approute_policy_name,description,dscp_value,sla_obj_id,primary_link_pref,alternate_link_pref)

    topo_obj_id=resp_topo.json()["definitionId"]
    approute_obj_id=resp_topo.json()["definitionId"]
     #print (json.dumps(resp_approute.json(),indent=2))
    resp_apply_policy=session.apply_approute_policy("EASTCoast_policy",approute_obj_id,site_obj_id,vpn_obj_id,topo_obj_id,description="New_VOIP_POLICY")
    new_policy_id=resp_apply_policy["policyId"]
    print (f"New policy created successfully : {new_policy_id}")

if __name__ == "__main__":
    main()

