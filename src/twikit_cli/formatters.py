#!/usr/bin/env python3
"""
JSON formatters for twikit objects - centralizes data extraction logic.

This module provides functions to convert twikit objects (Tweet, User) and
parsed article data into comprehensive dictionary structures for JSON output.
All functions handle missing data gracefully with safe accessors.
"""


def tweet_to_dict(tweet) -> dict:
    """
    Extract comprehensive tweet data from twikit Tweet object.

    Args:
        tweet: A twikit Tweet object

    Returns:
        dict: Enhanced tweet data with author, entities, media, relationships, metrics
    """
    # Core fields
    tweet_dict = {
        "id": getattr(tweet, 'id', None),
        "text": getattr(tweet, 'text', ''),
        "full_text": getattr(tweet, 'full_text', None) or getattr(tweet, 'text', ''),
        "created_at": getattr(tweet, 'created_at', None),
        "lang": getattr(tweet, 'lang', None),
    }

    # Author - complete user object (not just name/screen_name)
    user = getattr(tweet, 'user', None)
    if user:
        tweet_dict["author"] = user_to_dict(user, include_metrics=True)
    else:
        tweet_dict["author"] = None

    # Metrics - group all engagement metrics
    tweet_dict["metrics"] = {
        "reply_count": getattr(tweet, 'reply_count', 0) or 0,
        "retweet_count": getattr(tweet, 'retweet_count', 0) or 0,
        "favorite_count": getattr(tweet, 'favorite_count', 0) or 0,
        "quote_count": getattr(tweet, 'quote_count', None),
        "bookmark_count": getattr(tweet, 'bookmark_count', None),
        "view_count": getattr(tweet, 'view_count', None),
    }

    # Entities - hashtags, mentions, URLs with indices
    entities_obj = getattr(tweet, 'entities', None)
    if entities_obj and isinstance(entities_obj, dict):
        tweet_dict["entities"] = {
            "hashtags": [
                {
                    "text": h.get('text', ''),
                    "indices": h.get('indices', [])
                }
                for h in entities_obj.get('hashtags', [])
            ],
            "urls": [
                {
                    "url": u.get('url', ''),
                    "expanded_url": u.get('expanded_url', ''),
                    "display_url": u.get('display_url', ''),
                    "indices": u.get('indices', [])
                }
                for u in entities_obj.get('urls', [])
            ],
            "user_mentions": [
                {
                    "id": m.get('id_str') or m.get('id'),
                    "name": m.get('name', ''),
                    "screen_name": m.get('screen_name', ''),
                    "indices": m.get('indices', [])
                }
                for m in entities_obj.get('user_mentions', [])
            ],
        }
    else:
        tweet_dict["entities"] = {
            "hashtags": [],
            "urls": [],
            "user_mentions": [],
        }

    # Media - photos, videos with URLs and metadata
    media_list = getattr(tweet, 'media', None)
    if media_list and isinstance(media_list, list):
        tweet_dict["media"] = [
            {
                "type": m.get('type', 'unknown'),
                "url": m.get('url', ''),
                "media_url_https": m.get('media_url_https', ''),
                "expanded_url": m.get('expanded_url', ''),
            }
            for m in media_list
        ]
    else:
        # Also check entities.media (alternative location)
        if entities_obj and isinstance(entities_obj, dict):
            entities_media = entities_obj.get('media', [])
            tweet_dict["media"] = [
                {
                    "type": m.get('type', 'unknown'),
                    "url": m.get('url', ''),
                    "media_url_https": m.get('media_url_https', ''),
                    "expanded_url": m.get('expanded_url', ''),
                }
                for m in entities_media
            ]
        else:
            tweet_dict["media"] = []

    # Relationships - reply/quote/retweet tracking
    tweet_dict["relationships"] = {
        "in_reply_to_user_id": getattr(tweet, 'in_reply_to_user_id', None) or getattr(tweet, 'in_reply_to_user_id_str', None),
        "in_reply_to_status_id": getattr(tweet, 'in_reply_to_status_id', None) or getattr(tweet, 'in_reply_to_status_id_str', None),
        "quoted_status_id": getattr(tweet, 'quoted_status_id', None) or getattr(tweet, 'quoted_status_id_str', None),
        "is_quote_status": getattr(tweet, 'is_quote_status', False),
    }

    # Check if it's a retweet
    retweeted_tweet = getattr(tweet, 'retweeted_tweet', None)
    if retweeted_tweet:
        tweet_dict["relationships"]["is_retweet"] = True
        tweet_dict["relationships"]["retweeted_status_id"] = getattr(retweeted_tweet, 'id', None)
    else:
        tweet_dict["relationships"]["is_retweet"] = False
        tweet_dict["relationships"]["retweeted_status_id"] = None

    # Context - additional flags
    tweet_dict["context"] = {
        "possibly_sensitive": getattr(tweet, 'possibly_sensitive', False),
        "place": getattr(tweet, 'place', None),
    }

    # DEPRECATED fields for backward compatibility
    # Keep old top-level fields for smoother migration
    tweet_dict["user"] = tweet_dict["author"]  # DEPRECATED: use 'author' instead
    tweet_dict["retweet_count"] = tweet_dict["metrics"]["retweet_count"]  # DEPRECATED: use 'metrics.retweet_count'
    tweet_dict["favorite_count"] = tweet_dict["metrics"]["favorite_count"]  # DEPRECATED: use 'metrics.favorite_count'
    tweet_dict["reply_count"] = tweet_dict["metrics"]["reply_count"]  # DEPRECATED: use 'metrics.reply_count'

    return tweet_dict


def user_to_dict(user, include_metrics=True) -> dict:
    """
    Extract comprehensive user data from twikit User object.

    Args:
        user: A twikit User object
        include_metrics: Whether to include follower/following counts (default: True)

    Returns:
        dict: Complete user profile with images, verification, metrics
    """
    user_dict = {
        # Basic profile
        "id": getattr(user, 'id', None),
        "name": getattr(user, 'name', ''),
        "screen_name": getattr(user, 'screen_name', ''),
        "description": getattr(user, 'description', None) or '',
        "location": getattr(user, 'location', None) or '',
        "url": getattr(user, 'url', None),
        "created_at": getattr(user, 'created_at', None),

        # Images
        "profile_image_url": getattr(user, 'profile_image_url', None),
        "profile_banner_url": getattr(user, 'profile_banner_url', None),

        # Verification and status
        "verified": getattr(user, 'verified', False),
        "is_blue_verified": getattr(user, 'is_blue_verified', False),
        "protected": getattr(user, 'protected', False),
    }

    # Metrics - optional, as they may not always be needed
    if include_metrics:
        user_dict["followers_count"] = getattr(user, 'followers_count', 0) or 0
        # following_count might be stored as friends_count in some APIs
        user_dict["following_count"] = getattr(user, 'following_count', None) or getattr(user, 'friends_count', 0) or 0
        user_dict["statuses_count"] = getattr(user, 'statuses_count', 0) or 0
        user_dict["favourites_count"] = getattr(user, 'favourites_count', 0) or 0

    return user_dict


def article_to_dict(article_info) -> dict:
    """
    Convert parsed article data to structured JSON.

    Args:
        article_info: Dictionary returned by parse_article_content()

    Returns:
        dict: Structured article data with blocks, markdown, and plain text
    """
    if 'error' in article_info:
        return {
            "error": article_info['error']
        }

    # Build content blocks with type information
    content_blocks = []
    markdown_lines = []
    plain_text_parts = []

    for formatted_text in article_info.get('text_content', []):
        # Detect block type from formatting
        text = formatted_text.strip()

        if text.startswith('# '):
            block_type = 'header-one'
            clean_text = text[2:].strip()
        elif text.startswith('## '):
            block_type = 'header-two'
            clean_text = text[3:].strip()
        elif text.startswith('### '):
            block_type = 'header-three'
            clean_text = text[4:].strip()
        elif text.startswith('> '):
            block_type = 'blockquote'
            clean_text = text[2:].strip()
        elif text.startswith('• '):
            block_type = 'unordered-list-item'
            clean_text = text[2:].strip()
        elif text.startswith('```'):
            block_type = 'code-block'
            clean_text = text.strip('`').strip()
        else:
            block_type = 'unstyled'
            clean_text = text

        content_blocks.append({
            "type": block_type,
            "text": clean_text
        })

        markdown_lines.append(formatted_text)
        plain_text_parts.append(clean_text)

    return {
        "id": article_info.get('rest_id', ''),
        "title": article_info.get('title', ''),
        "preview_text": article_info.get('preview_text', ''),
        "cover_media_url": article_info.get('cover_media_url', ''),

        "content": {
            "blocks": content_blocks,
            "markdown": '\n'.join(markdown_lines),
            "plain_text": '\n\n'.join(plain_text_parts),
        }
    }


def gql_tweet_to_dict(tweet_result, legacy, user_result, user_legacy) -> dict:
    """
    Convert raw GQL API response data to enhanced tweet dictionary.

    This is specifically for the tweet get command which uses the GQL API
    and returns raw dictionary data instead of twikit Tweet objects.

    Args:
        tweet_result: The tweet result from GQL API
        legacy: The legacy field containing tweet data
        user_result: The user result from GQL API
        user_legacy: The legacy field containing user data

    Returns:
        dict: Enhanced tweet data matching the format of tweet_to_dict()
    """
    # Core fields
    tweet_dict = {
        "id": tweet_result.get("rest_id"),
        "text": legacy.get("full_text", ""),
        "full_text": legacy.get("full_text", ""),
        "created_at": legacy.get("created_at"),
        "lang": legacy.get("lang"),
    }

    # Author - complete user object
    tweet_dict["author"] = {
        "id": user_result.get("rest_id"),
        "name": user_legacy.get("name", ''),
        "screen_name": user_legacy.get("screen_name", ''),
        "description": user_legacy.get("description", '') or '',
        "location": user_legacy.get("location", '') or '',
        "url": user_legacy.get("url"),
        "created_at": user_legacy.get("created_at"),
        "profile_image_url": user_legacy.get("profile_image_url_https"),
        "profile_banner_url": user_legacy.get("profile_banner_url"),
        "verified": user_legacy.get("verified", False),
        "is_blue_verified": user_result.get("is_blue_verified", False),
        "protected": user_legacy.get("protected", False),
        "followers_count": user_legacy.get("followers_count", 0) or 0,
        "following_count": user_legacy.get("friends_count", 0) or 0,
        "statuses_count": user_legacy.get("statuses_count", 0) or 0,
        "favourites_count": user_legacy.get("favourites_count", 0) or 0,
    }

    # Metrics - including advanced metrics from GQL
    tweet_dict["metrics"] = {
        "reply_count": legacy.get("reply_count", 0) or 0,
        "retweet_count": legacy.get("retweet_count", 0) or 0,
        "favorite_count": legacy.get("favorite_count", 0) or 0,
        "quote_count": legacy.get("quote_count"),
        "bookmark_count": legacy.get("bookmark_count"),
        "view_count": tweet_result.get("views", {}).get("count"),
    }

    # Entities - extract from legacy.entities
    entities = legacy.get("entities", {})
    tweet_dict["entities"] = {
        "hashtags": [
            {
                "text": h.get('text', ''),
                "indices": h.get('indices', [])
            }
            for h in entities.get('hashtags', [])
        ],
        "urls": [
            {
                "url": u.get('url', ''),
                "expanded_url": u.get('expanded_url', ''),
                "display_url": u.get('display_url', ''),
                "indices": u.get('indices', [])
            }
            for u in entities.get('urls', [])
        ],
        "user_mentions": [
            {
                "id": m.get('id_str') or m.get('id'),
                "name": m.get('name', ''),
                "screen_name": m.get('screen_name', ''),
                "indices": m.get('indices', [])
            }
            for m in entities.get('user_mentions', [])
        ],
    }

    # Media - from entities.media
    media_list = entities.get('media', [])
    tweet_dict["media"] = [
        {
            "type": m.get('type', 'unknown'),
            "url": m.get('url', ''),
            "media_url_https": m.get('media_url_https', ''),
            "expanded_url": m.get('expanded_url', ''),
        }
        for m in media_list
    ]

    # Relationships
    tweet_dict["relationships"] = {
        "in_reply_to_user_id": legacy.get('in_reply_to_user_id_str') or legacy.get('in_reply_to_user_id'),
        "in_reply_to_status_id": legacy.get('in_reply_to_status_id_str') or legacy.get('in_reply_to_status_id'),
        "quoted_status_id": legacy.get('quoted_status_id_str') or legacy.get('quoted_status_id'),
        "is_quote_status": legacy.get('is_quote_status', False),
        "is_retweet": bool(legacy.get('retweeted_status_id_str') or legacy.get('retweeted_status_result')),
        "retweeted_status_id": legacy.get('retweeted_status_id_str'),
    }

    # Context
    tweet_dict["context"] = {
        "possibly_sensitive": legacy.get('possibly_sensitive', False),
        "place": legacy.get('place'),
    }

    # DEPRECATED fields for backward compatibility
    tweet_dict["user"] = tweet_dict["author"]  # DEPRECATED: use 'author' instead
    tweet_dict["retweet_count"] = tweet_dict["metrics"]["retweet_count"]  # DEPRECATED
    tweet_dict["favorite_count"] = tweet_dict["metrics"]["favorite_count"]  # DEPRECATED
    tweet_dict["reply_count"] = tweet_dict["metrics"]["reply_count"]  # DEPRECATED

    return tweet_dict
