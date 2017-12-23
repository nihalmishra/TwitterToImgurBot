from bs4 import BeautifulSoup
import pyimgur
import praw
from praw.models import Comment
import urllib
import re
import requests
import os
import time
import datetime as DateTime
import Secrets

### API ###

with open("run_logs.log", "a+") as log:
	
	#Log start time.
	time_stamp = DateTime.datetime.fromtimestamp(time.time())
	log.write("Run started at " + str(time_stamp) +"\n")
	log.write("--------------------------------------------------\n")
	
	#Connect to imgur
	try:
		imgur = pyimgur.Imgur(Secrets.IMGUR_CLIENT_ID, Secrets.IMGUR_CLIENT_SECRET, Secrets.IMGUR_ACCESS_TOKEN, Secrets.IMGUR_REFRESH_TOKEN)
		authorization_url = imgur.authorization_url('pin')
	except Exception:
		log.write("Exception occurred while initializing Imgur API.")
		exit()
		
	
	#Connect to reddit	
	try:
		reddit = praw.Reddit(client_id = Secrets.REDDIT_CLIENT_ID,
						client_secret = Secrets.REDDIT_CLIENT_SECRET,
 					    user_agent = "TwitterToImgurBot", 
 					    username = Secrets.REDDIT_USERNAME, 
 					    password = Secrets.REDDIT_PWD)
	except Exception:
		log.write("Exception occurred while initializing Reddit API")
		exit()

	
	#Obtain subreddit
	subreddit = reddit.subreddit("test")
	
	if not os.path.isfile("tti_posts_replied_to.txt"):
				posts_replied_to = []
	else:
		with open("tti_posts_replied_to.txt", "r") as f:
			posts_replied_to = f.read()
			posts_replied_to = posts_replied_to.split("\n")
			posts_replied_to = list(filter(None, posts_replied_to))

	for submission in subreddit.new(limit=100):
		
		print("Analyzing submission with id:" + submission.id)
		
		if submission.id in posts_replied_to:
			continue
		
		time.sleep(10)
		
		if submission.domain == "twitter.com":
			url = submission.url
			page = requests.get(url)
			soup = BeautifulSoup(page.text, "html.parser")
			tweet = soup.find('p', {'class': 'tweet-text'}).text

			soup_filter = str(soup.findAll('div', {'class': 'AdaptiveMedia-photoContainer'}))
			#print("soup_filter: " + soup_filter)
			image_url = re.findall('src=\"(.*?)\"', soup_filter)
			if image_url == []:
				continue
			tweet = tweet.split('pic.twitter.com', 1)[0]
			tweet = tweet.replace('#','/#')

			### UPLOAD IMAGE TO IMGUR, RETRIEVE URL ###
			images_id = ""
			album_id = ""
			if len(image_url) == 1:
				
				image_url = image_url[0]
				### UPLOAD IMAGE TO IMGUR, RETRIEVE URL ###
				ImgurImage = imgur.upload_image(url = image_url, title = submission.title)
				final_url = ImgurImage.link
				images_id = ImgurImage.id
				
			elif len(image_url) > 1:
				### UPLOAD IMAGES TO IMGUR, RETRIEVE ALBUM URL ###
	
				list_of_images = []
				for image in image_url:
					uploaded_image = imgur.upload_image(url = image, title = submission.title)
					list_of_images.append(uploaded_image)
					images_id = images_id + " " + uploaded_image.id
				#print(list_of_images)
				ImgurAlbum = imgur.create_album(title = "TwitterToImgurBot_Album", description = tweet, images = list_of_images)
				album_id = ImgurAlbum.id
				final_url = "https://imgur.com/a/" + ImgurAlbum.id
			#print(final_url)
			
			### POST TO REDDIT ###
			try:
				submission.reply('%s \n\n[Image Contained in Tweet](%s)\n***\n I am a bot beep boop.^(You can leave feedback by replying to me)' % (tweet, final_url))
				posts_replied_to.append(submission.id)
			except Exception as e:
				log.write("Error commenting on post: " + submission.id + ". \nError occurred: '" + e.message + "'\n")
				break
			
			print("Writing log:" + submission.id)
				
			log.write("PostID: " + submission.id +"\n")
			log.write("ImageId(s): " + images_id + "\n")
			log.write("AlbumId: " + album_id + "\n")
			log.write("--------------------------------------------------\n")
		
		else:
			continue
	
	log.write("===============================================================================\n")

with open("tti_posts_replied_to.txt", "w") as f:
	for post_id in posts_replied_to:
		print("Writing post:" + post_id)
		f.write(post_id + "\n")