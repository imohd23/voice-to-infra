from distutils.fancy_getopt import OptionDummy
import json
import boto3
import random
import string
import time
import logging
import requests
import urllib3
logging.getLogger().setLevel(logging.INFO)
def lambda_handler(event, context):
    commandsList = ['Create', 'Update', 'Delete']

    fileName = event['Records'][0]['s3']['object']['key']
    bucketName = 'mo-create-infra'

    transcribe = boto3.client('transcribe')
    letters = string.ascii_lowercase
    transcribeJobName= ''.join(random.choice(letters) for i in range(10))

    transcribeJob = transcribe.start_transcription_job(
        TranscriptionJobName=transcribeJobName,
        Media={
            'MediaFileUri': 's3://'+bucketName+'/'+fileName
        },
        IdentifyLanguage= True
    )
    time.sleep(10)
    complete = False
    while complete != True:
        jobStatus = transcribe.get_transcription_job(
            TranscriptionJobName= transcribeJobName
        )
        if jobStatus['TranscriptionJob']['TranscriptionJobStatus'] != 'COMPLETED':
            time.sleep(5)
        else:
            complete = True
    
    transcribeText = requests.get(jobStatus['TranscriptionJob']['Transcript']['TranscriptFileUri'])
    transcribeText = json.loads(transcribeText.text)
    transcribeText = transcribeText['results']['transcripts'][0]['transcript']
    
    transcribeText = transcribeText.split(' ')
    
    commandExists= False
    for i in commandsList:
        
        if i in transcribeText:
            commandExists = True
            commandIndex = transcribeText.index(i)
            commandName = transcribeText[commandIndex]
            print(i)
    
    if not commandExists:
        return "Command not supported"
    
    #? check the option index to find the option value
    optionIndex = transcribeText.index('Option')
    optionIndex = optionIndex + 1
    optionSelected = transcribeText[optionIndex]
    
    
    
    createInfra(commandName, optionSelected[:-1])

    return True



def configs(commandName, optionSelected):
    
    instances = [
        {
            "commandName":"Create",
            "option": "1",
            "params": {
                "instanceType": "t2.micro",
                "minCount": 1,
                "maxCount": 1,
                "imageId": "ami-0c1bc246476a5572b",
                "keyName": "temp"
            }
        },
        {
            "commandName":"Create",
            "option": "2",
            "params": {
                "instanceType": "t2.micro",
                "minCount": 1,
                "maxCount": 2,
                "imageId": "ami-0c1bc246476a5572b",
                "keyName": "temp"
            }
        }
    ]

    for i in instances:
        if i['commandName'] == commandName and int(i['option']) == int(optionSelected):
            return i['params']
    return False


def createInfra(commandName, optionSelected):
    ec2 = boto3.resource('ec2')

    instanceOptions = configs(commandName, optionSelected)

    try:
    
        ec2.create_instances(
                ImageId= instanceOptions['imageId'],
                MinCount= instanceOptions['minCount'],
                MaxCount= instanceOptions['maxCount'],
                InstanceType= instanceOptions['instanceType'],
                KeyName= instanceOptions['keyName']
            )
    
    except Exception as e:
        return "Option is not valid or something else happened."

