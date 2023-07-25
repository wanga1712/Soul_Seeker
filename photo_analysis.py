def get_photos(self, user_id, num_photos=3):
    # This function will retrieve the photos of the user with the given user_id
    # using the VKontakte API.

    method = 'photos.getAll'
    params = {
        'owner_id': user_id,
        'extended': 1,  # To get detailed information about each photo
        'photo_sizes': 1,  # To get different sizes of each photo
        'access_token': self.access_token,
        'v': '5.131'  # VK API version
    }

    response = requests.get(self.BASE_URL + method, params=params)
    data = response.json()

    if 'response' in data:
        # Sort photos by likes count in descending order
        items = data['response']['items']
        items.sort(key=lambda x: x.get("likes", {}).get("count", 0), reverse=True)

        # Get the top num_photos photos and extract their largest size URLs
        photos_urls = []
        for photo_info in items[:num_photos]:
            sizes = photo_info.get('sizes', [])
            if sizes:
                sizes.sort(key=lambda x: x.get("width", 0), reverse=True)
                largest_size_url = sizes[0].get("url")
                photos_urls.append(largest_size_url)

        return photos_urls
    else:
        raise ValueError(f"Error retrieving photos for user {user_id}: {data['error']['error_msg']}")