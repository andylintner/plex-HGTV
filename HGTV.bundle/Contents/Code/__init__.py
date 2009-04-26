import re, sys, urllib2
from PMS import Plugin, Log, DB, Thread, XML, HTTP, JSON, RSS, Utils
from PMS.MediaXML import *
from PMS.Shorthand import _L, _R, _E, _D

PLUGIN_PREFIX   = "/video/hgtv"

# Full Episode URLs
SHOW_LINKS_URL       = "http://www.hgtv.com/full-episodes/package/index.html"

# Clip URLs
BASE_URL        = "http://www.hgtv.com/"


CACHE_INTERVAL      = 2000

####################################################################################################
def Start():
  Plugin.AddRequestHandler(PLUGIN_PREFIX, HandleVideosRequest, "HGTV", "icon.jpg", "art.jpg")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", contentType="items")
  Plugin.AddViewGroup("List", viewMode="List", contentType="items")
##################################################################################################

def HandleVideosRequest(pathNouns, count): 
  try:
    title2 = pathNouns[count-1].split("||")[1]
    pathNouns[count-1] = pathNouns[count-1].split("||")[0]
  except:
    title2 = ""
    
  vg="InfoList"
  
  dir = MediaContainer("art-default.jpg", viewGroup=vg, title1="HGTV",title2=title2)
  
  if count == 0:
    shows = XML.ElementFromString(HTTP.GetCached(SHOW_LINKS_URL, CACHE_INTERVAL), True).xpath('//h2')
    for s in shows:
        title = s.text
        url = s.xpath("../p[@class='cta']/a")[0].get('href')
        thumb = s.xpath("../a/img")[0].get('src')
        dir.AppendItem(DirectoryItem('shows||'+url, title))
    
  
  elif pathNouns[0].startswith("shows"):
    target_url = BASE_URL+('/'.join(pathNouns[1:]))
    html = HTTP.GetCached(target_url, CACHE_INTERVAL)
    matches = re.search("SNI.HGTV.Player.FullSize\('vplayer-1','([^']*)'", html)
    show_id = matches.group(1)
    matches = re.search("mdManager.addParameter\(\"SctnId\",[\s]*\"([^\"]*)", html)
    sctn_id = matches.group(1)
    matches = re.search("mdManager.addParameter\(\"DetailId\",[\s]*\"([^\"]*)", html)
    detail_id = matches.group(1)
    clips = XML.ElementFromString(HTTP.GetCached('http://www.hgtv.com/hgtv/channel/xml/0,,'+show_id+',00.xml', CACHE_INTERVAL).strip(), False).xpath("//video")
    for c in clips:
        title = c.xpath("./clipName")[0].text
        duration = GetDurationFromDesc(c.xpath("length")[0].text)
        desc = c.xpath("abstract")[0].text
        url = 'http://www.hgtv.com/hgtv/video/player/0,1000149,HGTV_'
        url += sctn_id+'_'
        url += detail_id+'_'
        url += show_id+'-'
        url += c.xpath("./videoId")[0].text
        url += '.html'
        Log.Add(url)
        thumb = c.xpath("thumbnailUrl")[0].text
        vidItem = WebVideoItem(url, title, desc, duration, thumb)
        dir.AppendItem(vidItem)
        
  else:
        Log.Add("Unknown pathNoun: "+str(pathNouns))
    
    
  return dir.ToXML()
  
# Try and parse the duration from the end of the description
def GetDurationFromDesc(desc):
  duration = ""

  try:
    descArray =  desc.split("(")
    descArrayLen =  len (descArray)
    if descArrayLen<2:
      return ""

    time = descArray[descArrayLen - 1]
    timeArray = time.split(":")

    timeArrayLen = len(timeArray)

    if timeArrayLen<2:
      return ""

    minutes = int(timeArray[0])
    seconds = int(timeArray[1].split(")")[0])
    duration = str(((minutes*60) + seconds)*1000)
    
  except:
    # There was a problem getting the duration (maybe it isn't on the description any more?) so quit with a null
    return ""

  return duration
