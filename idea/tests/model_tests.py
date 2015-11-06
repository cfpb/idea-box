from django.test import TestCase
from idea import models
from datetime import datetime
from idea.tests.utils import random_user, create_superuser
from core.custom_comments.models import MPTTComment


class VotingTests(TestCase):
    fixtures = ['state']

    def setUp(self):
        create_superuser()
        self.state = models.State.objects.get(name='Active')

    def test_members(self):
        user = random_user()
        idea = models.Idea(creator=user, title='Transit subsidy to Mars',
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        self.assertEqual(len(idea.members), 1)
        self.assertIn(user, idea.members)

    def test_members_with_voters(self):
        user = random_user()
        idea = models.Idea(creator=user, title='Transit subsidy to Mars',
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        voter = random_user()
        self.assertNotEqual(user, voter)
        vote = models.Vote()
        vote.idea = idea
        vote.creator = voter
        vote.save()

        self.assertEqual(len(idea.members), 1)
        self.assertNotIn(voter, idea.members)
        self.assertIn(user, idea.members)

    def test_members_with_comments(self):
        user = random_user()
        idea = models.Idea(creator=user, title='Transit subsidy to Mars',
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        commenter = random_user()
        self.assertNotEqual(user, commenter)
        comment = MPTTComment()
        comment.user = commenter
        comment.content_object = idea
        comment.comment = 'Test'
        comment.is_public = True
        comment.is_removed = False
        comment.site_id = 1
        comment.submit_date = datetime.now()
        comment.save()

        self.assertEqual(len(idea.members), 2)
        self.assertIn(commenter, idea.members)
        self.assertIn(user, idea.members)

    def test_members_with_comment_by_same_user(self):
        user = random_user()
        idea = models.Idea(creator=user, title='Transit subsidy to Mars',
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        commenter = user

        comment = MPTTComment()
        comment.user = commenter
        comment.content_object = idea
        comment.comment = 'Test'
        comment.is_public = True
        comment.is_removed = False
        comment.site_id = 1
        comment.submit_date = datetime.now()
        comment.save()

        self.assertEqual(len(idea.members), 1)
        self.assertIn(user, idea.members)
