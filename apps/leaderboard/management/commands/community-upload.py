from django.db.models.query_utils import Q
import sys
from django.db import transaction
from django.core.management.base import BaseCommand
import requests
import json
from apps.atpace_community.models import Comment, Post, SpaceGroups, SpaceMembers, Spaces
from apps.users.models import User, UserTypes
from .circle_data import circle_member, circle_member_search, circle_parent_comment, circle_post, circle_post_comments, circle_space, circle_space_group, create_member, upload_cover_images

class Command(BaseCommand):
    help = "Update default data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        community_id = 22900
        space_id = 165387
        space_group_id = 51976
        admin = User.objects.get(username="admin")
        user_type = UserTypes.objects.get(type="Learner")

        # circle member migrations here
        space_group_data = circle_space_group(community_id, space_group_id)
        try:
            space_group = SpaceGroups.objects.get(title=space_group_data['name'])
        except SpaceGroups.DoesNotExist:
            space_group = SpaceGroups.objects.create(title=space_group_data['name'], hidden_from_non_members=space_group_data['is_hidden_from_non_members'], privacy="Public", created_by=admin)
            self.stdout.write(self.style.SUCCESS("Space Group Created!"))

        space_data = circle_space(community_id, space_id)
        privacy = "Private" if space_data['is_private'] else "Public"
        try:
            space = Spaces.objects.get(title=space_data['name'])
        except Spaces.DoesNotExist:
            space = Spaces.objects.create(title=space_data['name'], space_group=space_group, privacy=privacy, created_by=admin)
            self.stdout.write(self.style.SUCCESS("Space Created!"))

        i=1
        while i<3:
            space_members_data = circle_member(i)
            if not space_members_data:
                self.stdout.write(self.style.SUCCESS("No Member available!"))
            for member in space_members_data:
                response = create_member(member, space, space_group)
                
                if response:
                    self.stdout.write(self.style.SUCCESS("User Created!"))
                    self.stdout.write(self.style.SUCCESS("Space Member Created!"))
                else:
                    self.stdout.write(self.style.SUCCESS("User Already Exist!"))
            i+=1
        post_data = circle_post(community_id, space_id)
        if not post_data:
            self.stdout.write(self.style.SUCCESS("No Post available!"))
        for p_data in post_data:
            user = circle_member_search(community_id, p_data['user_email'], space, space_group)
            if user==False:
                continue
            title = p_data['name'] or ''
            is_liking_enabled = p_data['is_liking_enabled'] or True
            post = Post.objects.create(title=title, Body=p_data['body']['body'], post_type="Post",
                    is_comments_enabled=p_data['is_comments_enabled'], is_liking_enabled=is_liking_enabled, space=space, space_group=space_group, created_by=user)
            post.created_at=p_data['body']['created_at']
            post.updated_at=p_data['body']['updated_at']
            if p_data['cover_image_url']:
                file_name, cover_image = upload_cover_images(p_data['cover_image_url'])
                post.cover_image.save(file_name, cover_image)
            post.save()
            self.stdout.write(self.style.SUCCESS(f"{post.title} Post Created!"))
            if p_data['comments_count']>0:
                post_id = p_data['id']
                comment_data = circle_post_comments(community_id, space_id, post_id)
                for com_data in comment_data:
                    commentor = circle_member_search(community_id, com_data['user_email'], space, space_group)
                    if commentor==False:
                        continue
                    comment = Comment.objects.create(Body=com_data['body']['body'], post=post, created_by=commentor)
                    comment.created_at=com_data['body']['created_at']
                    comment.updated_at=com_data['body']['updated_at']
                    comment.save()
                    self.stdout.write(self.style.SUCCESS("Comment Created!"))
                    if com_data['parent_comment_id']:
                        parent_comment = circle_parent_comment(community_id, com_data['parent_comment_id'])
                        commentor = circle_member_search(community_id, parent_comment['user_email'], space, space_group)
                        if commentor==False:
                            continue
                        comment_parent_id = Comment.objects.create(Body=parent_comment['body']['body'], post=post, created_by=commentor)
                        comment_parent_id.created_at=com_data['body']['created_at']
                        comment_parent_id.updated_at=com_data['body']['updated_at']
                        comment_parent_id.save()
                        self.stdout.write(self.style.SUCCESS("Parent Comment Created!"))
                        comment.parent_id = comment_parent_id
                        comment.save()