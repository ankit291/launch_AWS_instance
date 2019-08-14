import boto3
import time
import os
import sys
Host_Name=sys.argv[1]
#import pdb;pdb.set_trace()

ec2 = boto3.resource('ec2',region_name='us-east-1')

def create_ec2_instance():

    instance = ec2.create_instances(
        ImageId='ami-09b932d39fb3f395b',
        MinCount=1,
        MaxCount=1,
        Monitoring={
            'Enabled': False},
        InstanceType='t2.micro',
        KeyName='cointreau-prod',
        SecurityGroupIds=['sg-fece1185','sg-5d2beb26','sg-8cd379f7'],
        SubnetId='subnet-39384e61',
        IamInstanceProfile={
            'Name': 'cointreau-jobsub-prod-use1-profile',
            },
    )
    ID = instance[0].id
    
    def get_status():
            client = boto3.client('ec2')
	    Status=client.describe_instances(InstanceIds=[ID])['Reservations'][0]['Instances'][0]['State']['Name']
	    priv_IP=client.describe_instances(InstanceIds=[ID])['Reservations'][0]['Instances'][0]['PrivateIpAddress']
            rev_IP='.'.join(reversed(priv_IP.split('.')))

    	    while Status=="pending":
        	    time.sleep(10)
        	    Status=client.describe_instances(InstanceIds=[ID])['Reservations'][0]['Instances'][0]['State']['Name']
    
    	    if Status == 'running':
        	    print "Now you can add tag your instance"
		    response = client.create_tags(
		    	Resources=[ID],	
			Tags=[{'Key':'Env','Value': 'prod'},{'Key': 'Location', 'Value': 'use1'},{'Key':'Name','Value': Host_Name},
			      {'Key':'Profile','Value': 'jobsub'},{'Key':'approval','Value': 'planned'},{'Key':'department','Value': 'mpe'},
		              {'Key':'environment','Value': 'prod'},{'Key':'note','Value': 'comscore instances'},{'Key':'owner','Value': 'comscoresupport@3pillarglobal.com'},
	       	              {'Key':'project','Value': 'comscore Project'},]
		            )
	    
	    ins_tags=client.describe_instances(InstanceIds=[ID])['Reservations'][0]['Instances'][0]['Tags']
	    ins_Name = [i['Value'] for i in ins_tags if i['Key'] == 'Name'][0]
            print ins_Name
            response = boto3.client('route53').change_resource_record_sets(
            	HostedZoneId='Z2M2UW7JU6RG2I',
            	ChangeBatch={
	                'Changes': [
        	            {
                	        'Action': 'CREATE',
                	        'ResourceRecordSet': {
                	            'Name': ins_Name +'.',
                	            'Type': 'A',
                	            'TTL': 300,
                	            'ResourceRecords': [
                	                  {
                	                  'Value': priv_IP
                	                  },
                	              ],
                	          }
                	     },
          	       ]
         	 }
    	     )

            responseR = boto3.client('route53').change_resource_record_sets(
        	    HostedZoneId='Z18N13E7MFE9LD',
        	    ChangeBatch={
                	'Changes': [
                	    {
                	        'Action': 'CREATE',
                	        'ResourceRecordSet': {
                	            'Name': rev_IP + '.in-addr.arpa.',
                	            'Type': 'PTR',
                	            'TTL': 180,
                	            'ResourceRecords': [
                	                {
                	                'Value': ins_Name
                        	        },
                  	      	    ],
                  	      }
                  	  },
               	     ]
                }
           )
            cmd = 'export ANSIBLE_HOST_KEY_CHECKING=False; ansible-playbook -i /Users/ankit.tyagi/PYTHON_JOBSUB/inv changes.yml --extra-vars "job_Server='+ ins_Name +' hostd=' + priv_IP +'"'
            os.system(cmd)
    get_status()
if __name__ == '__main__':
    create_ec2_instance()
