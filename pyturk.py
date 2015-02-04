#!/usr/bin/env python
# Copyright (c) 2010 Nathan Morris, nathan.ms@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

# toolbox for mturk
# http://docs.amazonwebservices.com/AWSMechanicalTurkRequester/2008-08-02/


import time
import hmac
import sha
import base64
import urllib
import xml.dom.minidom

AWS_ACCESS_KEY_ID = 'YOUR KEY HERE'
AWS_SECRET_ACCESS_KEY = 'YOUR SECRET HERE'
SERVICE_NAME = 'AWSMechanicalTurkRequester'
SERVICE_VERSION = '2008-08-02'

SANDBOXP = False


# Define authentication routines
def generate_timestamp(gmtime):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", gmtime)


def generate_signature(service, operation, timestamp, secret_access_key):
    sig = service + operation + timestamp
    my_sha_hmac = hmac.new(secret_access_key, sig, sha)
    my_b64_hmac_digest = base64.encodestring(my_sha_hmac.digest()).strip()
    return my_b64_hmac_digest


def req(operation, args=None):
    # Calculate the request authentication parameters
    timestamp = generate_timestamp(time.gmtime())
    signature = generate_signature('AWSMechanicalTurkRequester', operation,
                                   timestamp, AWS_SECRET_ACCESS_KEY)

    # Construct the request
    parameters = {
        'Service': SERVICE_NAME,
        'Version': SERVICE_VERSION,
        'AWSAccessKeyId': AWS_ACCESS_KEY_ID,
        'Timestamp': timestamp,
        'Signature': signature,
        'Operation': operation
    }

    if args:
        parameters.update(args)

    # Make the request
    if SANDBOXP:
        url = 'http://mechanicalturk.sandbox.amazonaws.com'
    else:
        url = 'http://mechanicalturk.amazonaws.com'
    result_xmlstr = urllib.urlopen(url, urllib.urlencode(parameters)).read()
    return result_xmlstr


def errcheck(result_xml):
    # Check for and print results and errors
    errors_nodes = result_xml.getElementsByTagName('Errors')
    if errors_nodes:
        print 'There was an error processing your request:'
        for errors_node in errors_nodes:
            for error_node in errors_node.getElementsByTagName('Error'):
                print('  Error code:    ' +
                      error_node.getElementsByTagName('Code')[0].childNodes[0].data)
                print('  Error message: ' +
                      error_node.getElementsByTagName('Message')[0].childNodes[0].data)
    return errors_nodes


def pp(string):
    result_xml = xml.dom.minidom.parseString(string)
    return result_xml


def GetAccountBalance():
    result_xmlstr = req(operation='GetAccountBalance')
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    availbalance_nodes = result_xml.getElementsByTagName('AvailableBalance')
    if availbalance_nodes:
        print("Available balance: " +
              availbalance_nodes[0].getElementsByTagName('FormattedPrice')[0].childNodes[0].data)
    return availbalance_nodes[0].getElementsByTagName('FormattedPrice')[0].childNodes[0].data


def UpdateQualificationScore(SubjectId=None, IntegerValue=70,
                             QualificationTypeId=None):
    parameters = {
        'QualificationTypeId': QualificationTypeId,
        'SubjectId': SubjectId,
        'IntegerValue': IntegerValue,
    }
    result_xmlstr = req(operation='UpdateQualificationScore', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return isvalid


# Make the request
def CreateQualificationType(Name, Description, QualificationTypeStatus='Active',
                            AutoGranted='true', AutoGrantedValue=70):

    """
        # sample parameters
        Name="GrammarGrading"
        Description="English proofreading and editing test"
        QualificationTypeStatus = 'Active'
        AutoGranted = 'true'
        AutoGrantedValue = 50
    """
    parameters = {
        'Name': Name,
        'Description': Description,
        'QualificationTypeStatus': QualificationTypeStatus,
        'AutoGranted': AutoGranted,
        'AutoGrantedValue': AutoGrantedValue,
    }
    result_xmlstr = req(operation='CreateQualificationType',  args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)

    # get unique qualification id and return it
    QualificationTypeId = result_xml.getElementsByTagName('QualificationTypeId')[0].childNodes[0].data
    return dict(QualificationTypeId=QualificationTypeId)


def GetReviewableHITs(PageSize=100, PageNumber=1):
    parameters = {
        'PageSize': PageSize,
        'PageNumber': PageNumber,
    }
    result_xmlstr = req(operation='GetReviewableHITs',  args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    node_hits = result_xml.getElementsByTagName('HITId')
    HIT = []
    for i in node_hits:
        HIT.append(i.childNodes[0].nodeValue)
    TotalNumResults = result_xml.getElementsByTagName('TotalNumResults')[0].childNodes[0].data
    return dict(TotalNumResults=TotalNumResults, HIT=HIT)


def GetAssignmentsForHIT(HITId, PageSize=100, PageNumber=1):
    parameters = {
        'HITId': HITId,
        'PageSize': PageSize,
        'PageNumber': PageNumber,
    }
    result_xmlstr = req(operation='GetAssignmentsForHIT',  args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    AssignmentId = result_xml.getElementsByTagName('AssignmentId')
    WorkerId = result_xml.getElementsByTagName('WorkerId')
    AssignmentStatus = result_xml.getElementsByTagName('AssignmentStatus')
    Assignment = []
    for i in range(len(AssignmentId)):
        Assignment.append(
            {'AssignmentId': AssignmentId[i].childNodes[0].data,
             'AssignmentStatus': AssignmentStatus[i].childNodes[0].data,
             'WorkerId': WorkerId[i].childNodes[0].data}
            )
    return Assignment


def ApproveAssignment(AssignmentId):
    parameters = {
        'AssignmentId': AssignmentId,
    }
    result_xmlstr = req(operation='ApproveAssignment',  args=parameters)
    print result_xmlstr
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return result_xml


def AssignQualification(
        QualificationTypeId='412ZJ2X42XTZYCG0AZYZ',
        WorkerId='A2S40QZMC988QF',
        IntegerValue=None, SendNotification=None):

    parameters = {
        'QualificationTypeId': QualificationTypeId,
        'WorkerId': WorkerId,
    }
    if IntegerValue:
        parameters['IntegerValue'] = IntegerValue
    if SendNotification:
        parameters['SendNotification'] = SendNotification
    result_xmlstr = req(operation='AssignQualification',  args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def DisposeHIT(HITId):
    parameters = {
        'HITId': HITId,
    }
    result_xmlstr = req(operation='DisposeHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def GetHIT(HITId):
    parameters = {
        'HITId': HITId,
    }
    result_xmlstr = req(operation='GetHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    AssignmentDurationInSeconds = result_xml.childNodes[0].\
        getElementsByTagName('AssignmentDurationInSeconds')[0].childNodes[0].data
    HITReviewStatus = result_xml.childNodes[0].\
        getElementsByTagName('HITReviewStatus')[0].childNodes[0].data
    CreationTime = result_xml.childNodes[0].\
        getElementsByTagName('CreationTime')[0].childNodes[0].data
    HITStatus = result_xml.childNodes[0].\
        getElementsByTagName('HITStatus')[0].childNodes[0].data
    Reward = result_xml.childNodes[0].getElementsByTagName('Reward')[0].\
        childNodes[0].childNodes[0].data
    return dict(AssignmentDurationInSeconds=AssignmentDurationInSeconds,
                HITReviewStatus=HITReviewStatus,
                CreationTime=CreationTime,
                HITStatus=HITStatus,
                Reward=Reward)


def SetHITAsReviewing(HITId, Revert=False):
    parameters = {
        'HITId': HITId,
        'Revert': Revert,
    }
    result_xmlstr = req(operation='SetHITAsReviewing', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def BlockWorker(WorkerId, Reason=None):
    if Reason != None:
        Reason = "poor performance" # just a default reason
    parameters = {
        'WorkerId': WorkerId,
        'Reason': Reason,
    }
    result_xmlstr = req(operation='BlockWorker', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def UnblockWorker(WorkerId, Reason=None):
    if Reason:
        Reason = "improved performance" # just a default reason
    parameters = {
        'WorkerId': WorkerId,
        'Reason': Reason,
    }
    result_xmlstr = req(operation='UnblockWorker', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def ChangeHITTypeOfHIT(HITId, HITTypeId):
    # HITTypeId, the ID of the new HIT type
    parameters = {
        'HITId': HITTypeId,
        'HITTypeId': HITTypeId,
    }
    result_xmlstr = req(operation='ChangeHITTypeOfHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


#CreateHIT only works for offsite hits now. QualificationRequirement LocaleVale and RequiredToPreview options too
def CreateHIT(HITTypeId=None, Question=None, LifetimeInSeconds=60*60*24*2,
              MaxAssignments=None, RequesterAnnotation=None, Title="test01",
              Description="test01",  Reward=0.01, AssignmentDurationInSeconds=3600,
              AutoApprovalDelayInSeconds=12*60*60, Keywords=None,
              QualificationRequirement=None):
    parameters = {
        'Question': Question,
        'LifetimeInSeconds': LifetimeInSeconds,
        'Title': Title,
        'Description': Description,
        'Reward.1.Amount': Reward,
        'Reward.1.CurrencyCode': 'USD',
        'AssignmentDurationInSeconds': AssignmentDurationInSeconds,
    }
    #optionsal parameters
    if HITTypeId:
        parameters['HITTypeId'] = HITTypeId
    if MaxAssignments:
        parameters['MaxAssignments'] = MaxAssignments
    if RequesterAnnotation:
        parameters['RequesterAnnotation'] = RequesterAnnotation
    if Keywords:
        parameters['Keywords']=Keywords
    #QualificationRequirement is a list of dictionaries
    if QualificationRequirement:
          for i in range(len(QualificationRequirement)):
                parameters['QualificationRequirement.' + str(i+1) + '.QualificationTypeId']=\
                                             QualificationRequirement[i]['QualificationTypeId']
                parameters['QualificationRequirement.' + str(i+1) + '.Comparator']=\
                                             QualificationRequirement[i]['Comparator']
                if QualificationRequirement[i]['IntegerValue']:
                    parameters['QualificationRequirement.' + str(i+1) + '.IntegerValue']=\
                                                 QualificationRequirement[i]['IntegerValue']
                if QualificationRequirement[i]['LocaleValue']:
                    parameters['QualificationRequirement.' + str(i+1) + '.LocaleValue.Country']=\
                                                 QualificationRequirement[i]['LocaleValue']
    if AutoApprovalDelayInSeconds:
        parameters['AutoApprovalDelayInSeconds']=AutoApprovalDelayInSeconds
    result_xmlstr = req(operation='CreateHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    HITId = result_xml.childNodes[0].getElementsByTagName('HITId')[0].childNodes[0].data
    HITTypeId = result_xml.childNodes[0].getElementsByTagName('HITTypeId')[0].childNodes[0].data
    return dict(isvalid=isvalid, HITId=HITId, HITTypeID=HITTypeId)


def DisableHIT(HITId):
    # HITTypeId, the ID of the new HIT type
    parameters = {
        'HITId': HITId,
    }
    result_xmlstr = req(operation='DisableHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def DisposeQualificationType(QualificationTypeId):
    # HITTypeId, the ID of the new HIT type
    parameters = {
        'QualificationTypeId': QualificationTypeId,
    }
    result_xmlstr = req(operation='DisposeQualificationType', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def ExtendHIT(HITId, MaxAssignmentsIncrement=None,
              ExpirationIncrementInSeconds=None):
   #required parameters
    parameters = {
        'HITId': HITId,
    }
    #optionsal parameters
    if MaxAssignmentsIncrement:
        parameters['MaxAssignmentsIncrement'] = MaxAssignmentsIncrement
    if ExpirationIncrementInSeconds:
        parameters['ExpirationIncrementInSeconds'] = ExpirationIncrementInSeconds
    result_xmlstr = req(operation='ExtendHIT',  args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def ForceExpireHIT(HITId):
    parameters = {
        'HITId': HITId,
    }
    result_xmlstr = req(operation='ForceExpireHIT', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


# todo: finish parsing response
def GetBonusPayments(HITId=None, AssignmentId=None,
                     PageSize=100, PageNumber=1):
    #function needs HITId or AssignmentId
    parameters = {
    }
    if HITId:
          parameters['HITId'] = HITId
    elif AssignmentId != None:
          parameters['AssignmentId'] = AssignmentId
    result_xmlstr = req(operation='GetBonusPayments', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    return dict(result_xmlstr=result_xmlstr)


# todo: need to test and finish parsing response
def GetFileUploadURL(AssignmentId,QuestionIdentifier):
    parameters = {
        'AssignmentId': AssignmentId,
        'QuestionIdentifier':  QuestionIdentifier,
    }
    result_xmlstr = req(operation='GetFileUploadURL', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    return result_xmlstr


# todo: need to finish parsing reponse
def GetHITsForQualificationType(QualificationTypeId, PageSize=100,
                                PageNumber=1):
    parameters = {
        'QualificationTypeId': QualificationTypeId,
    }
    result_xmlstr = req(operation='GetHITsForQualificationType', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    return result_xmlstr


# todo: need to finish parsing response
def GetQualificationsForQualificationType(QualificationTypeId, Status=None,
                                          PageSize=100, PageNumber =1):
    parameters = {
        'QualificationTypeId': QualificationTypeId,
    }
    # optionsal parameters
    if Status:
        parameters['Status'] = Status
    result_xmlstr = req(operation='GetQualificationsForQualificationType',
                        args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid, result_xmlstr=result_xmlstr)


# todo need to finish parsing response 
def GetQualificationRequests(QualificationTypeId=None, SortProperty=None,
                             SortDirection=None,PageSize=100, PageNumber=1):
    parameters = {
        'PageSize': PageSize,
        'PageNumber': PageNumber,
    }
    # optionsal parameters
    if QualificationTypeId:
        parameters['QualificationTypeId'] = QualificationTypeId
    if SortProperty:
        parameters['SortProperty'] = SortProperty
    if SortDirection:
        parameters['SortDirection'] = SortDirection
    if SortDirection:
        parameters['SortDirection'] = SortDirection
    result_xmlstr = req(operation='GetQualificationRequests', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid, result_xmlstr=result_xmlstr)


def GetQualificationScore(QualificationTypeId, SubjectId):
    parameters = {
        'QualificationTypeId': QualificationTypeId,
        'SubjectId': SubjectId,
    }
    result_xmlstr = req(operation='GetQualificationScore', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    IntegerValue = result_xml.childNodes[0].getElementsByTagName('IntegerValue')[0].childNodes[0].data
    return dict(IntegerValue=IntegerValue)


# todo parse response
def GetQualificationType(QualificationTypeId):
    parameters = {
        'QualificationTypeId': QualificationTypeId,
    }
    result_xmlstr = req(operation='GetQualificationType', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    return dict(result_xmlstr=result_xmlstr)


# todo to parse response and test
def GetRequesterStatistic(Statistic, TimePeriod='OneDay', Count=1):
    #TimePeriod, Valid Values: OneDay | SevenDays | ThirtyDays | LifeToDate
    #Count conditional if TimePeriod = OneDay
    parameters = {
        'Statistic': Statistic,
        'TimePeriod': TimePeriod,
    }
    if TimePeriod == "OneDay":
        parameters['Count']=Count
    result_xmlstr = req(operation='GetRequesterStatistic', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    return dict(result_xmlstr=result_xmlstr)


def GrantBonus(WorkerId, AssignmentId, BonusAmount=0.05, Reason="gave 110%"):
    parameters = {
        'WorkerId': WorkerId,
        'AssignmentId': AssignmentId, 
        'BonusAmount.1.Amount': BonusAmount,
        'BonusAmount.1.CurrencyCode': 'USD',
        'Reason': Reason,
    }
    result_xmlstr = req(operation='GrantBonus', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


# todo test
def GrantQualification(QualificationRequestId, IntegerValue=1):
    parameters = {
        'QualificationRequestId': QualificationRequestId,
        'IntegerValue': IntegerValue, 
    }
    result_xmlstr = req(operation='GrantQualification', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


# todo test
def NotifyWorkers(Subject, MessageText, WorkerId):
    #WorkerId must be a list of WorkerId strings 
    parameters = {
        'Subject': Subject,
        'MessageText': MessageText,
    }
    for i in range(len(WorkerId)):
           parameters['WorkerId.'+str(i+1)] = WorkerId[i]
    result_xmlstr = req(operation = 'NotifyWorkers',  args = parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


# todo test (parsing probably wrong)
def RegisterHITType(Title="Complete a survey", 
                    Description="Complete a survey. Fill in all information",
                    Reward=0.01, AssignmentDurationInSeconds=3600,
                    Keywords=None,  AutoApprovalDelayInSeconds=None, QualificationRequirement=None):
        parameters = {
            'Title': Title,
            'Description': Description,
            'Reward.1.Amount': Reward,
            'Reward.1.CurrencyCode': 'USD',
            'AssignmentDurationInSeconds': AssignmentDurationInSeconds,
        }
        # optionsal parameters
        if Keywords:
            parameters['Keywords'] = Keywords
        if QualificationRequirement:
            parameters['QualificationRequirement'] = QualificationRequirement
        if AutoApprovalDelayInSeconds:
            parameters['AutoApprovalDelayInSeconds'] = AutoApprovalDelayInSeconds
        result_xmlstr = req(operation='RegisterHITType', args=parameters)
        result_xml = pp(result_xmlstr)
        errors = errcheck(result_xml)
        isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
        HITTypeId = result_xml.childNodes[0].getElementsByTagName('HITTypeId')[0].childNodes[0].data
        return dict(isvalid=isvalid, HITTypeID=HITTypeId)


def RejectAssignment(AssignmentId, RequesterFeedback=None):
    # RequesterFeedback is an optional message for the user (string)
    parameters = {
        'AssignmentId': AssignmentId,
    }
    if RequesterFeedback:
         parameters['RequesterFeedback']=RequesterFeedback
    result_xmlstr = req(operation = 'RejectAssignment',  args = parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid = isvalid)


# todo test
def RejectQualificationRequest(QualificationRequestId, Reason=None):
    # Reason is an optional message for the user (string)
    parameters = {
        'QualificationRequestId' : QualificationRequestId,
    }
    if Reason:
         parameters['Reason'] = Reason
    result_xmlstr = req(operation='RejectQualificationRequest',
                        args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid = isvalid)


def RevokeQualification(SubjectId, QualificationTypeId, Reason=None):
    # Reason is an optional message for the user (string)
    parameters = {
    'SubjectId' : SubjectId,
    'QualificationTypeId' : QualificationTypeId, 
    }
    if Reason:
         #Reason = urllib.quote(Reason)
         parameters['Reason'] = Reason
    result_xmlstr = req(operation='RevokeQualification', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid)


def SearchHITs(PageSize=100, PageNumber=1, SortDirection='Descending',
               SortProperty='Expiration'):
    parameters = {
        'PageSize' : PageSize,
        'PageNumber' : PageNumber,
        'SortDirection' : SortDirection,
        'SortProperty' : SortProperty
    }
    result_xmlstr = req(operation='SearchHITs', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    HIT = []
    for i in range(len(result_xml.childNodes[0].getElementsByTagName('HITId'))):
               HIT.append({'HITId' : result_xml.childNodes[0].getElementsByTagName('HITId')[i].childNodes[0].data,\
                            'CreationTime': result_xml.childNodes[0].getElementsByTagName('CreationTime')[i].childNodes[0].data,
                            'MaxAssignments':result_xml.childNodes[0].getElementsByTagName('MaxAssignments')[i].childNodes[0].data})
    return HIT


#need to test and parse response
def SearchQualificationTypes(Query=None, SortProperty=None, SortDirection=None,
                             PageSize=100, PageNumber=1, MustBeRequestable=True,
                            MustBeOwnedByCaller=True  ):
    parameters = {
        'PageSize': PageSize,
        'PageNumber': PageNumber,
        'MustBeRequestable': MustBeRequestable,
        'MustBeOwnedByCaller' : MustBeOwnedByCaller,
    }
    if Query:
         parameters['Query'] = Query
    if SortProperty:
        parameters['SortProperty'] = SortProperty
    if SortDirection:
        parameters['SortDirection'] = SortDirection
    result_xmlstr = req(operation='SearchQualificationTypes', args=parameters)
    result_xml = pp(result_xmlstr)
    errors = errcheck(result_xml)
    isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
    return dict(isvalid=isvalid, result_xmlstr=result_xmlstr)


#need to test, update parsing response, fix request for AnswerKey, Test
def UpdateQualificationType(QualificationTypeId, RetryDelayInSeconds=None,
                            QualificationTypeStatus=None, Description=None,
                            Test=None, AnswerKey=None, TestDurationInSeconds=None,
                            AutoGranted=None, AutoGrantedValue=None):
            parameters = {
                'QualificationTypeId' : QualificationTypeId,
            }
            if RetryDelayInSeconds:
                parameters['RetryDelayInSeconds'] = RetryDelayInSeconds
            if QualificationTypeStatus:
                parameters['QualificationTypeStatus'] = QualificationTypeStatus
            if Description:
                 parameters['Description'] = Description
            if Test:
                parameters['Test'] = Test
            if Test:  
                parameters['AnswerKey'] = AnswerKey
            if TestDurationInSeconds:
                parameters['TestDurationInSeconds'] = TestDurationInSeconds
            if AutoGranted:
                parameters['AutoGranted'] = AutoGranted
            result_xmlstr = req(operation='UpdateQualificationType', args=parameters)
            result_xml = pp(result_xmlstr)
            errors = errcheck(result_xml)
            isvalid = result_xml.childNodes[0].getElementsByTagName('IsValid')[0].childNodes[0].data
            return dict(isvalid = isvalid,  result_xmlstr=result_xmlstr)

#todo: add functions SetHITTypeNotification, SendTestEventNotification
#all functions below here not in AWS API

# creates Question data 
def externalQuestion(url, frame_height=None):
    if frame_height == None:
        frame_height = 800
    return """<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
            <ExternalURL>""" + url + """</ExternalURL>
            <FrameHeight>""" + str(frame_height) + """</FrameHeight>
            </ExternalQuestion>"""


#generate a list of dicts of qualifications for CreateHIT
def genQual(QualificationTypeId, Comparator='GreaterThan', IntegerValue=50):
           return [dict(QualificationTypeId=QualificationTypeId,
                        Comparator=Comparator, IntegerValue=IntegerValue)]
