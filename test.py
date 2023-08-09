import cli
import time
from datetime import datetime

#Configure tftp server and direcory
dst="ftp://calo:calo@10.124.154.60:/temp/"

#List of commands
cmd_list=[
"sh ver | i uptime|Installation mode|Cisco IOS Software",
"sh redundancy | i ptime|Location|Current Software state",
"sh processes cpu platform sorted | i wncd",
"sh platform resources",
"show process memory platform sorted",
"show processes memory platform accounting",
"sh platform",
"sh inventory",
"sh environment",
"show license summary | i Status:",
"sh ap sum | i Number of APs",
"sh ap uptime | ex ____([0-9])+ day",
"sh ap crash",
"sh wireless stats ap session termination",
"show wireless stats ap history | i Disjoined",
"sh ap tag summary | i  Yes",
"show ap sum sort descending client-count | i __0__",
"sh wireless summary",
"sh wireless stats client detail | i Authenticating         :|Mobility               :|IP Learn               :|Webauth Pending        :|Run                    :|Delete-in-Progress     :",
"sh wireless stats client delete reasons | e : 0",
"sh wireless stats trace-on-failure",
"show radius statistics",
"sh aaa servers | i Platform Dead: total|RADIUS: id",
"sh ap dot11 5ghz summary",
"sh ap dot11 24ghz summary",
"sh ap auto-rf dot11 5ghz | i Channel changes due to radar|AP Name|Channel Change Count",
"sh ap auto-rf dot11 24ghz | i Channel Change Count|AP Name",
"sh ap dot11 5ghz load-info",
"sh ap dot11 24ghz load-info",
"sh platform hardware chassis active qfp statistics drop",
"show platform hardware chassis active qfp feature wireless punt statistics",
"sh buffers | i buffers|failures",
"show platform hardware chassis active qfp datapath utilization | i Load",
"show wireless mobility sum",
"sh nmsp status"
]


#List of commands require several outputs
multiple_cmd_list=[
"sh wireless stats client delete reasons | e : 0",
"show radius statistics",
"sh buffers | i buffers|failures",
"sh platform hardware chassis active qfp statistics drop",
"show platform hardware chassis active qfp feature wireless punt statistics"
]

def Generate_file_name():
    #Return file_name equal to hostname-date_time.txt
    now = datetime.now()
    #Get hostname
    hostname=cli.cli("sh ver | i uptime is").split()[0]
    file_name = hostname+"-"+str(now.strftime("%b-%d-%Y-%H-%M"))+".txt"
    return file_name

def Execute_command (cmd):
    #Return command+timestamp+output
    output="\n\nCMD: "+cmd+"\n\n"
    output+=cli.cli("sh clock")
    output+=cli.cli(cmd)
    return(output)

def Export_Log(file_name):
    #Export the file generated
    export_cmd="copy bootflash:/guest-share/"+file_name+" "+dst+""
    cli.cli(export_cmd)
    print ("Exported files "+file_name+" to destination "+dst+"")

def Delete_Log(file_name):
    #Delete file generated
    delete_cmd="delete bootflash:/guest-share/"+file_name+" ; "
    cli.cli(delete_cmd)
    print ("Deleted files "+file_name+"")

def Find_platform_redundancy_interface():
    #Check platform type
    platform=cli.cli("sh platform | i Chassis type").split()[-1]
    print (platform)
    #Check redundancy
    standby=cli.cli("show chassis | i Standby*.*Ready")
    if "9800-40" in platform or "9800-80" in platform:
        cmd_list.insert(2,"dir harddisk:/core/ | i core|system-report")
        if standby:
            cmd_list.insert(3,"dir stby-harddisk:/core/ | i core|system-report")
        cmd_list.insert(4,"sh processes cpu platform sorted | ex 0%      0%      0%")
    if "9800-CL" in platform or "9800-L" in platform:
        cmd_list.insert(2,"dir bootflash:/core/ | i core|system-report")
        if standby:
            cmd_list.insert(3,"dir stby-bootflash:/core/ | i core|system-report")
    #Find the interface or portchanel for wireless mgmt SVI
    Wireless_Mgmt_Vlan = cli.cli("sh wi interface summary | i Management")
    if Wireless_Mgmt_Vlan:
        Wireless_Mgmt_Vlan = Wireless_Mgmt_Vlan.split()[2]
        Interface_cmd = "sh vlan id "+Wireless_Mgmt_Vlan+" | i active"
        Interface=cli.cli(Interface_cmd).split()[-1]
        cmd="sh int "+Interface+" | i line protocol|put rate|drops|broadcast"
        cmd_list.insert(len(cmd_list)-7,cmd)
    #Find interface version to change telemetry command
    version=cli.cli("sh ver | i Cisco IOS Software")
    images=["Version 16.12","Version 17.1","Version 17.2","Version 17.3","Version 17.4","Version 17.5","Version 17.6","Version 17.7","Version 17.8","Version 17.9","Version 17.10","Version 17.11","Version 17.12"]
    if any(x in version for x in images):
        cmd="sh telemetry internal connection"
        cmd_list.insert(len(cmd_list)-1,cmd)
    else:
        cmd="sh telemetry connection all"
        cmd_list.insert(len(cmd_list)-1,cmd)

def main():
    print ("Starting datacollection")
    file_name=Generate_file_name()
    file_name_path="/bootflash/guest-share/"+file_name+""
    Find_platform_redundancy_interface()
    with open(file_name_path, 'w') as f:
        for command in cmd_list:
            #print (command)
            f.write(Execute_command(command))
        if multiple_cmd_list:
            for i in range(5):
                for command in multiple_cmd_list:
                    f.write(Execute_command(command))
                time.sleep(5)
    f.close()
    #Export file generated
    Export_Log(file_name)
    #Execute more command of the file to see outputs of the file can be commentted if output is too long
    more_cmd="more bootflash:/guest-share/"+file_name+""
    print (cli.cli(more_cmd))
    #Delete file
    Delete_Log(file_name)
    
if __name__ == "__main__":
    main()
