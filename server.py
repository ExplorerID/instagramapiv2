from flask import Flask, request, jsonify
from instagram_private_api import Client, ClientCompatPatch
import uuid
import random
import string
import requests
import tempfile
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder

app = Flask(__name__)

# Map to store tokens and corresponding Instagram clients
token_client_map = {}


def authenticate(username, password):
    device_id = str(uuid.uuid4())
    api = Client(username, password, auto_patch=True, authenticate=True, device_id=device_id)
    api.login()
    token = api.authenticated_user_id

    token_client_map[token] = api

    return token


@app.route("/authenticate", methods=["POST"])
def authenticate_user():
    username = request.json.get("username")
    password = request.json.get("password")
    token = authenticate(username, password)
    return jsonify({"user_id": token})


@app.route("/getUserProfile", methods=["GET"])
def get_user_profile():
    token = request.headers.get("Authorization")
    api = token_client_map.get(token)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    user_profile = api.user_info(token)["user"]
    return jsonify(user_profile)


def generate_rank_token(user_id):
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{user_id}_{random_string}"

@app.route("/getUserFollowers", methods=["GET"])
def get_user_followers():
    user_id = request.headers.get("Authorization")
    api = token_client_map.get(user_id)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    rank_token = api.generate_uuid()
    user_followers = api.user_followers(user_id, rank_token=rank_token)["users"]
    followers_list = [user["username"] for user in user_followers]
    return jsonify(followers_list)


@app.route("/getUserFollowings", methods=["GET"])
def get_user_followings():
    user_id = request.headers.get("Authorization")
    api = token_client_map.get(user_id)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    rank_token = api.generate_uuid()    
    user_followings = api.user_following(user_id, rank_token=rank_token)["users"]
    followings_list = [user["username"] for user in user_followings]
    return jsonify(followings_list)


@app.route("/followUser", methods=["POST"])
def follow_user():
    token = request.headers.get("Authorization")
    api = token_client_map.get(token)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    user_id = request.json.get("user_id")
    api.friendships_create(user_id)
    return jsonify({"status": "success"})


@app.route("/unfollowUser", methods=["POST"])
def unfollow_user():
    token = request.headers.get("Authorization")
    api = token_client_map.get(token)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    user_id = request.json.get("user_id")
    api.friendships_destroy(user_id)
    return jsonify({"status": "success"})


@app.route("/getUserPosts", methods=["GET"])
def get_user_posts():
    user_id = request.headers.get("Authorization")
    api = token_client_map.get(user_id)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    user_posts = api.user_feed(user_id)["items"]
    posts = []
    for post in user_posts:
        post_data = {
            "id": post["id"],
            "image_url": post.get("image_versions2", {}).get("candidates", [])[0].get("url", ""),
            "caption": post.get("caption", {}).get("text", "")
        }
        posts.append(post_data)
    return jsonify(posts)



@app.route("/postLike", methods=["POST"])
def post_like():
    token = request.headers.get("Authorization")
    api = token_client_map.get(token)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    media_id = request.json.get("media_id")
    api.post_like(media_id)
    return jsonify({"status": "success"})


@app.route("/postComment", methods=["POST"])
def post_comment():
    token = request.headers.get("Authorization")
    api = token_client_map.get(token)
    if not api:
        return jsonify({"error": "Invalid token"}), 401

    media_id = request.json.get("media_id")
    text = request.json.get("text")
    api.post_comment(media_id, text)
    return jsonify({"status": "success"})



if __name__ == "__main__":
    app.run()
