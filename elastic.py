from flask import current_app as app
import pygeoip, datetime
import hashlib
import ipaddress
import base64
import json
import magic
import botocore.session, botocore.client
from botocore.exceptions import ClientError


from flask_elasticsearch import FlaskElasticsearch

##################
# PUT ES Variables
##################

countries = ["AD","Andorra","AE","United Arab Emirates","AG","Antigua and Barbuda","AI","Anguilla","AL","Albania","AM","Armenia","AO","Angola","AQ","Antarctica","AR","Argentina","AS","American Samoa","AT","Austria","AU","Australia","AW","Aruba","AX","Åland Islands","AZ","Azerbaijan","BA","Bosnia and Herzegovina","BB","Barbados","BD","Bangladesh","BE","Belgium","BF","Burkina Faso","BG","Bulgaria","BH","Bahrain","BI","Burundi","BJ","Benin","BL","Saint Barthélemy","BM","Bermuda","BN","Brunei Darussalam","BO","Bolivia, Plurinational State of","BQ","Bonaire, Sint Eustatius and Saba","BR","Brazil","BS","Bahamas","BT","Bhutan","BV","Bouvet Island","BW","Botswana","BY","Belarus","BZ","Belize","CA","Canada","CC","Cocos (Keeling) Islands","CD","Congo, the Democratic Republic of the","CF","Central African Republic","CG","Congo","CH","Switzerland","CI","Côte d'Ivoire","CK","Cook Islands","CL","Chile","CM","Cameroon","CN","China","CO","Colombia","CR","Costa Rica","CU","Cuba","CV","Cape Verde","CW","Curaçao","CX","Christmas Island","CY","Cyprus","CZ","Czech Republic","DE","Germany","DJ","Djibouti","DK","Denmark","DM","Dominica","DO","Dominican Republic","DZ","Algeria","EC","Ecuador","EE","Estonia","EG","Egypt","EH","Western Sahara","ER","Eritrea","ES","Spain","ET","Ethiopia","FI","Finland","FJ","Fiji","FK","Falkland Islands (Malvinas)","FM","Micronesia, Federated States of","FO","Faroe Islands","FR","France","GA","Gabon","GB","United Kingdom","GD","Grenada","GE","Georgia","GF","French Guiana","GG","Guernsey","GH","Ghana","GI","Gibraltar","GL","Greenland","GM","Gambia","GN","Guinea","GP","Guadeloupe","GQ","Equatorial Guinea","GR","Greece","GS","South Georgia and the South Sandwich Islands","GT","Guatemala","GU","Guam","GW","Guinea-Bissau","GY","Guyana","HK","Hong Kong","HM","Heard Island and McDonald Islands","HN","Honduras","HR","Croatia","HT","Haiti","HU","Hungary","ID","Indonesia","IE","Ireland","IL","Israel","IM","Isle of Man","IN","India","IO","British Indian Ocean Territory","IQ","Iraq","IR","Iran, Islamic Republic of","IS","Iceland","IT","Italy","JE","Jersey","JM","Jamaica","JO","Jordan","JP","Japan","KE","Kenya","KG","Kyrgyzstan","KH","Cambodia","KI","Kiribati","KM","Comoros","KN","Saint Kitts and Nevis","KP","Korea, Democratic People's Republic of","KR","Korea, Republic of","KW","Kuwait","KY","Cayman Islands","KZ","Kazakhstan","LA","Lao People's Democratic Republic","LB","Lebanon","LC","Saint Lucia","LI","Liechtenstein","LK","Sri Lanka","LR","Liberia","LS","Lesotho","LT","Lithuania","LU","Luxembourg","LV","Latvia","LY","Libya","MA","Morocco","MC","Monaco","MD","Moldova, Republic of","ME","Montenegro","MF","Saint Martin (French part)","MG","Madagascar","MH","Marshall Islands","MK","Macedonia, the Former Yugoslav Republic of","ML","Mali","MM","Myanmar","MN","Mongolia","MO","Macao","MP","Northern Mariana Islands","MQ","Martinique","MR","Mauritania","MS","Montserrat","MT","Malta","MU","Mauritius","MV","Maldives","MW","Malawi","MX","Mexico","MY","Malaysia","MZ","Mozambique","NA","Namibia","NC","New Caledonia","NE","Niger","NF","Norfolk Island","NG","Nigeria","NI","Nicaragua","NL","Netherlands","NO","Norway","NP","Nepal","NR","Nauru","NU","Niue","NZ","New Zealand","OM","Oman","PA","Panama","PE","Peru","PF","French Polynesia","PG","Papua New Guinea","PH","Philippines","PK","Pakistan","PL","Poland","PM","Saint Pierre and Miquelon","PN","Pitcairn","PR","Puerto Rico","PS","Palestine, State of","PT","Portugal","PW","Palau","PY","Paraguay","QA","Qatar","RE","Réunion","RO","Romania","RS","Serbia","RU","Russian Federation","RW","Rwanda","SA","Saudi Arabia","SB","Solomon Islands","SC","Seychelles","SD","Sudan","SE","Sweden","SG","Singapore","SH","Saint Helena, Ascension and Tristan da Cunha","SI","Slovenia","SJ","Svalbard and Jan Mayen","SK","Slovakia","SL","Sierra Leone","SM","San Marino","SN","Senegal","SO","Somalia","SR","Suriname","SS","South Sudan","ST","Sao Tome and Principe","SV","El Salvador","SX","Sint Maarten (Dutch part)","SY","Syrian Arab Republic","SZ","Swaziland","TC","Turks and Caicos Islands","TD","Chad","TF","French Southern Territories","TG","Togo","TH","Thailand","TJ","Tajikistan","TK","Tokelau","TL","Timor-Leste","TM","Turkmenistan","TN","Tunisia","TO","Tonga","TR","Turkey","TT","Trinidad and Tobago","TV","Tuvalu","TW","Taiwan, Province of China","TZ","Tanzania, United Republic of","UA","Ukraine","UG","Uganda","UM","United States Minor Outlying Islands","US","United States","UY","Uruguay","UZ","Uzbekistan","VA","Vatican City State","VC","Saint Vincent and the Grenadines","VE","Venezuela, Bolivarian Republic of","VG","Virgin Islands, British","VI","Virgin Islands, U.S.","VN","Viet Nam","VU","Vanuatu","WF","Wallis and Futuna","WS","Samoa","YE","Yemen","YT","Mayotte","ZA","South Africa","ZM","Zambia","ZW","Zimbabwe",
            "", ""]



##################
# ES PUT functions
##################

def getCache(cacheItem, cache, cacheType):
    cacheTypeItem = cacheType + ":" + cacheItem
    rv = cache.get(cacheTypeItem)
    app.logger.debug("Returning item from cache: {0} - Value: {1}".format(cacheTypeItem, str(rv)[:200]+" ..."))
    if rv is None:
        return False
    return rv

def setCache(cacheItem, cacheValue, cacheTimeout, cache, cacheType):
  try:
      cacheTypeItem = cacheType + ":" + cacheItem
      cache.set(cacheTypeItem, cacheValue, timeout=cacheTimeout)
      app.logger.debug("Setting item to cache: {0} - Value: {1}".format(cacheTypeItem, str(cacheValue)[:200] + " ..."))
  except:
        app.logger.error("Could not set memcache cache {0} to value {1} and Timeout {2}".format(cacheTypeItem, str(cacheValue), cacheTimeout))


def getCountries(id):
    """return the country name for country code"""
    for i in range (0,len(countries) - 2, 2):
         shortCode = countries[i]
         countryName = countries[i+1]

         if (shortCode in id):
             return countryName

    return ""



def getGeoIPNative(sourceip, cache):

    """ get geoip and ASN information from IP """

    gi = pygeoip.GeoIP("/var/lib/GeoIP/GeoLite2-Country.mmdb")
    giCity = pygeoip.GeoIP("/var/lib/GeoIP/GeoLite2-City.mmdb")
    giASN = pygeoip.GeoIP('/var/lib/GeoIP/GeoLite2-ASN.mmdb')

    ASN_fail = "-"
    country_fail = "-"
    ASN_fail_text = "-"

    try:
        if ipaddress.ip_address(sourceip).is_private:
            ASN_fail="IANA"
            ASN_fail_text="IANA Private IP Range"
            country_fail = "PIR"

        asn = giASN.org_by_addr(sourceip)
        if (asn == "" ) or asn is None:
            setCache(sourceip, "0.0" + "|" + "0.0" + "|" + country_fail + "|" + ASN_fail + "|" + ASN_fail_text, 60 * 60 * 24, cache, "ip")
            return ("0.0", "0.0", "-", "-", "-")

        country = gi.country_code_by_addr(sourceip)
        if (country == "") or country is None:
            setCache(sourceip, "0.0" + "|" + "0.0" + "|" + country_fail + "|" + ASN_fail + "|" + ASN_fail_text, 60 * 60 * 24, cache, "ip")
            return ("0.0", "0.0", "-", "-", "-")

        long = giCity.record_by_addr(sourceip)['longitude']
        lat = giCity.record_by_addr(sourceip)['latitude']
        countryName = getCountries(country)
        asn = giASN.org_by_addr(sourceip)

        # store data in memcache
        setCache(sourceip, str(lat) + "|" + str(long) + "|" + country + "|"+ asn  + "|" + countryName, 60*60*24, cache, "ip")

        return (lat, long, country, asn, countryName)

    except:
        setCache(sourceip, "0.0" + "|" + "0.0" + "|" + country_fail + "|" + ASN_fail + "|" + ASN_fail_text, 60 * 60 * 24, cache, "ip")
        return ("0.0", "0.0", country_fail, ASN_fail, ASN_fail_text)





def getGeoIP(ip,cache):
    """ get geoip and ASN information from IP """

    # get result from cache
    getCacheResult = getCache(ip, cache, "ip")
    if getCacheResult is False:
        return getGeoIPNative(ip, cache)

    data = getCacheResult.split("|");

    return (data[0], data[1], data[2], data[3], data[4])


def ipExisting(ip, index, es):
    """ checks if an IP already is existing in the index """
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "default_field": "ip",
                            "query": ip
                        }
                    }
                ],
                "must_not": [],
                "should": []
            }
        },
        "from": 0,
        "size": 10,
        "sort": [],
        "aggs": {}
    }
    res = es.search(index=index, doc_type="IP", body=query)

    for hit in res['hits']['hits']:
        return True

    return False

def putIP(ip, esindex, country, countryname, asn, debug, es):
    """store the ip in the index"""
    m = hashlib.md5()
    m.update((ip).encode())

    vuln = {
        "asn": asn,
        "countryname": countryname,
        "ip": ip,
        "country": country

    }

    if debug:
        app.logger.debug("Not storing ip: " + str(ip))
        return True

    try:
        res = es.index(index=esindex, doc_type='IP', id=m.hexdigest(), body=vuln)
        return True

    except:
        app.logger.error("Error when persisting IP: " + str(ip))
        return False



def getFuzzyHash(packetdata, packetHash):

    packetdata = str(base64.b64decode(packetdata))

    if ('Host:' in packetdata):

        start = packetdata.find("Host:") + 5
        end = packetdata.find('\\', start)

        if end != -1:
            cleanedData = packetdata[0:start] + packetdata[end:len(packetdata)]
            cleanedData = str(cleanedData)

            m = hashlib.sha256()
            m.update(cleanedData.lower().encode('utf-8'))

            return m.hexdigest()

    return packetHash



def handlePacketData(packetdata, id, createTime, debug, es, sourceip, destport, s3client):
    m = hashlib.md5()
    try:
        decodedPayload = base64.decodebytes(packetdata.encode('utf-8'))
    except:
        app.logger.debug("Could not base64-decode payload from alert id %s." % id)
        return False

    m.update(decodedPayload)
    packetHash = m.hexdigest()
    lastSeenTime = createTime
    fuzzyHashCount=0
    count=1
    fileMagic="unknown"

    with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
        try:
            fileMagic=(m.id_buffer(decodedPayload))
        except:
            app.logger.debug("Could not determine MIME for payload %s." % packetHash)

    # check if packet is existing in index via hash
    statusContent, packetContent = packetExisting(packetHash, "payloads", es, debug, "hash")

    # check if packet is existing in index via fuzzyhash
    fuzzyHash=getFuzzyHash(packetdata, packetHash)
    statusFuzzy, fuzzyHashContent = packetExisting(fuzzyHash, "payloads", es, debug, "hashfuzzyhttp")

    if not(statusContent or statusFuzzy):
        app.logger.debug("Unable to work with ES (handlePacketData)")
        return False;

    if (packetContent and statusContent):
        app.logger.debug("Packet with same md5 hash %s already existing. Adjusting counts."  % packetHash)

        id = packetContent['_id']
        destport = packetContent['_source']['initialDestPort']
        sourceip = packetContent['_source']['initialIP']
        fuzzyHashCount=packetContent['_source']['fuzzyHashCount']
        packetHash = packetContent['_source']['hash']
        # update count and lastseen
        count=packetContent['_source']['md5count']+1
        if createTime > packetContent['_source']['createTime']:
            lastSeenTime = createTime
            createTime = packetContent['_source']['createTime']
        else:
            createTime = packetContent['_source']['createTime']
            lastSeenTime = packetContent['_source']['lastSeen']

    elif (fuzzyHashContent and statusFuzzy):
        app.logger.debug("Packet with same fuzzyHash %s already existing. Adjusting counts."  % fuzzyHash)

        id = fuzzyHashContent['_id']
        destport = fuzzyHashContent['_source']['initialDestPort']
        sourceip = fuzzyHashContent['_source']['initialIP']
        count = fuzzyHashContent['_source']['md5count']
        packetHash = fuzzyHashContent['_source']['hash']

        # update count and lastseen
        fuzzyHashCount=fuzzyHashContent['_source']['fuzzyHashCount']+1
        if createTime > fuzzyHashContent['_source']['createTime']:
            lastSeenTime = createTime
            createTime = fuzzyHashContent['_source']['createTime']
        else:
            lastSeenTime = fuzzyHashContent['_source']['lastSeen']
            createTime = fuzzyHashContent['_source']['createTime']




    # if fuzzyHashContent:
    #     app.logger.error('FuzzyHash known, not storing attack: %s' % fuzzyHash)
    # elif packetContent:
    #     app.logger.error('MD5 known, not storing attack from %s : %s' % (sourceip, packetHash))
    # else:
    #     app.logger.error("Found new payload from %s : %s" % (sourceip, packetHash))


    # store to s3
    if s3client and (not packetContent and not fuzzyHashContent):
        try:
            # upload file to s3
            s3client.put_object(Bucket=app.config['S3BUCKET'], Body=decodedPayload, Key=packetHash)
            app.logger.debug(
                'Storing file ({0}) using s3 bucket "{1}" on {2}'.format(packetHash,
                                                                         app.config['S3BUCKET'],
                                                                         app.config['S3ENDPOINT']))

        except ClientError as e:
            app.logger.error("Received error: %s", e.response['Error']['Message'])
    else:
        app.logger.debug("Not storing md5 {0} / FuzzyHash {1} to s3 as it is already present in packets index.".format(packetHash, fuzzyHash))

    packet = {
        "data" : "raw payload in s3",
        "createTime" : createTime,
        "lastSeen" : lastSeenTime,
        "hash" : packetHash,
        "hashfuzzyhttp": fuzzyHash,
        "initialIP" : sourceip,
        "md5count" : count,
        "fuzzyHashCount": fuzzyHashCount,
        "initialDestPort" : destport,
        "fileMagic" : fileMagic
    }

    if debug:
        app.logger.debug("Not sending out " + "Packet" + ": " + str(packet))
        return True

    try:
        app.logger.debug("Storing/Updating packet in index packets (handlePacketData)")

        res = es.index(index="payloads", doc_type="Packet", id=id, body=packet, refresh=True)
        return True

    except:
        app.logger.error("Error persisting packet in ES packet index: " + str(packet))
        return False

""" true on ok, false on error """
def putVuln(vulnid, index, sourceip, destinationip, createTime, tenant, url, analyzerID, peerType, username, password, loginStatus, version, startTime, endTime, sourcePort, destinationPort, externalIP, internalIP, hostname, sourceTransport, additionalData, debug, es, cache, packetdata, rawhttp, s3client):

    status, content = cveExisting(vulnid, index, es, debug)

    if (status):
        return True
    else:
        return putDoc(vulnid, index, sourceip, destinationip, createTime, tenant, url, analyzerID, peerType, username, password, loginStatus, version, startTime, endTime, sourcePort, destinationPort, externalIP, internalIP, hostname, sourceTransport, additionalData, debug, es, cache, "CVE", packetdata, rawhttp, s3client)


def putAlarm(vulnid, index, sourceip, destinationip, createTime, tenant, url, analyzerID, peerType, username, password, loginStatus, version, startTime, endTime, sourcePort, destinationPort, externalIP, internalIP, hostname, sourceTransport, additionalData, debug, es, cache, packetdata, rawhttp, s3client):
    return putDoc(vulnid, index, sourceip, destinationip, createTime, tenant, url, analyzerID, peerType, username, password, loginStatus, version, startTime, endTime, sourcePort, destinationPort, externalIP, internalIP, hostname, sourceTransport, additionalData, debug, es, cache, "Alert", packetdata, rawhttp, s3client)


def putDoc(vulnid, index, sourceip, destinationip, createTime, tenant, url, analyzerID, peerType, username, password, loginStatus, version, startTime, endTime, sourcePort, destinationPort, externalIP, internalIP, hostname, sourceTransport, additionalData, debug, es, cache, docType, packetdata, rawhttp, s3client):
    """stores an alarm in the index"""

    m = hashlib.md5()
    m.update((createTime + sourceip + destinationip + url + analyzerID + docType).encode())

    (lat, long, country, asn, countryName) = getGeoIP(sourceip, cache)
    (latDest, longDest, countryTarget, asnTarget, countryTargetName) = getGeoIP(destinationip, cache)

    currentTime = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


    if (len(str(packetdata)) > 0):
        # process payloads up to 5MB
        if (len(str(packetdata)) <= 5242880):
            if ("honeytrap" in peerType or "Dionaea" in peerType or "Webpage" in peerType):
                if ("ewscve" not in index):
                    status = handlePacketData(packetdata, m.hexdigest(), createTime, debug, es, sourceip, destinationPort, s3client)
                    if (status == False):
                        return False


    alert = {
        "country": country,
        "countryName": countryName,
        "vulnid": '%s' % vulnid,
        "originalRequestString": '%s' % url,
        "sourceEntryAS": asn,
        "createTime": createTime,
        "clientDomain": tenant,
        "peerIdent": analyzerID,
        "peerType": peerType,
        "client": "-",
        "location": str(lat) + " , " + str(long),
        "locationDestination": str(latDest) + " , " + str(longDest),
        "sourceEntryIp": sourceip,
        "sourceEntryPort": sourcePort,
        "additionalData": json.dumps(additionalData),
        "targetEntryIp": destinationip,
        "targetEntryPort": destinationPort,
        "targetCountry": countryTarget,
        "targetCountryName": countryTargetName,
        "targetEntryAS": asnTarget,
        "username": username,  # for ssh sessions
        "password": password,  # for ssh sessions
        "login": loginStatus,  # for SSH sessions
        "targetport": sourceTransport, # transport protocol (udp/tcp) targetPORT > targetPROT(ocol) ;)
        "clientVersion": version,
        "sessionStart": startTime,
        "sessionEnd": endTime,
        "recievedTime": currentTime,
        "externalIP": externalIP,
        "internalIP": internalIP,
        "hostname": hostname,
        "rawhttp": rawhttp
    }

    if debug:
        app.logger.debug("Not sending out " + docType + ": " + str(alert))
        return True

    try:
        res = es.index(index=index, doc_type=docType, id=m.hexdigest(), body=alert)

        # TODO Abbildung von handlePacketData

        return True

    except:
        app.logger.error("Error persisting alert in ES: " + str(alert))
        return False


def cveExisting(cve, index, es, debug):
    """ check if cve already exists in index """

    # if debug:
    #     app.logger.debug("Pretending as if %s was existing in index." % str(cve))
    #     return True, False

    query = """{
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "vulnid.keyword": "%s"                        }
                    }
                ]
            }
        },
        "from": 0,
        "size": 1,
        "sort": [],
        "aggs": {}
    }""" % cve


    try:
        res = es.search(index=index, doc_type="CVE", body=query)

        for hit in res['hits']['hits']:
            return True, (hit)
        return True, False

    except Exception as e:
        app.logger.error("Error querying ES for CVE vulnid: %s - Exception: %s" % (str(cve), str(e)))
        return False, False


def packetExisting(hash, index, es, debug, hashType):
    """ check if packet already exists in index """
    query = """{
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "%s" : "%s"
                        }
                    }
                ]
            }
        },
        "from": 0,
        "size": 1,
        "sort": [],
        "aggs": {}
    }""" % (hashType, hash)

    try:
        res = es.search(index=index, doc_type="Packet", body=query)
        for hit in res['hits']['hits']:
            return True, (hit)
        return True, False

    except Exception as e:
        app.logger.error("Error querying ES for packet with hash %s - Exception: %s" % (str(hash), str(e)))
        return False, False


