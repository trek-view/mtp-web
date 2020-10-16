def get_mapper_label(image_count=0):
    if image_count == 0:
        return 0
    if image_count <= 10:
        return 1
    if image_count <= 100:
        return 2
    if image_count <= 1000:
        return 3
    if image_count <= 10000:
        return 4
    if image_count <= 100000:
        return 5
    if image_count <= 1000000:
        return 6
    return 7


def get_guidebook_label(guidebook_count=0):
    if guidebook_count == 0:
        return 0
    if guidebook_count <= 5:
        return 1
    if guidebook_count <= 10:
        return 2
    if guidebook_count <= 20:
        return 3
    if guidebook_count <= 50:
        return 4
    if guidebook_count <= 100:
        return 5
    if guidebook_count <= 200:
        return 6
    return 7


def get_finder_label(image_view_point_count=0):
    if image_view_point_count == 0:
        return 0
    if image_view_point_count <= 10:
        return 1
    if image_view_point_count <= 50:
        return 2
    if image_view_point_count <= 100:
        return 3
    if image_view_point_count <= 200:
        return 4
    if image_view_point_count <= 500:
        return 5
    if image_view_point_count <= 1000:
        return 6
    return 7


def get_spotter_label(image_tag_count=0):
    if image_tag_count == 0:
        return 0
    if image_tag_count <= 10:
        return 1
    if image_tag_count <= 100:
        return 2
    if image_tag_count <= 1000:
        return 3
    if image_tag_count <= 10000:
        return 4
    if image_tag_count <= 100000:
        return 5
    if image_tag_count <= 1000000:
        return 6
    return 7

