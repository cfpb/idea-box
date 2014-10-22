from django.core.urlresolvers import reverse
from django.test import TestCase
from idea import models
from idea.tests.utils import random_user, login, create_superuser


class VotingTests(TestCase):
    fixtures = ['state']

    def setUp(self):
        create_superuser()
        self.state = models.State.objects.get(name='Active') 

    def test_good_vote(self):
        user = random_user()
        idea = models.Idea(creator=user, title='Transit subsidy to Mars', 
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        login(self)

        resp = self.client.post(reverse('idea:upvote_idea'), {'idea_id':idea.id, 'next':reverse('idea:idea_detail', args=(idea.id,))})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(idea.vote_set.all()), 1)

    def test_like_display(self):
        user = random_user()
        idea = models.Idea(creator=user, title='We need more meetings', 
                    text='Seriously - more meetings are productivity++.', state=self.state)
        idea.save()

        self.client.login(username='test1@example.com', password='1')

        resp = self.client.post(reverse('idea:upvote_idea'), {'idea_id':idea.id, 'next':reverse('idea:idea_detail', args=(idea.id,))})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(idea.vote_set.all()), 1)

    def test_vote_twice(self):
        """
            When a vote exists from a user, the user should see the "Liked" button.
            When another vote_up function is called, the user should see the "Like" button
            and the initial vote should be deleted.
        """
        idea = models.Idea(creator=random_user(), title='Transit subsidy to Mars', 
                    text='Aliens need assistance.', state=self.state)
        idea.save()

        #Login and create a vote
        login(self)
        resp = self.client.post(reverse('idea:upvote_idea'), {'idea_id':idea.id, 'next':reverse('idea:idea_detail', args=(idea.id,))})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(idea.vote_set.all()), 1)
        
        #Check to see that the vote appears, and that button displays liked
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertContains(resp, 'value="Liked" id="vote_down"', status_code=200, html=False)

        #Click unlike and remove the vote and confirm it doesn't exist
        resp = self.client.post(reverse('idea:upvote_idea'), {'idea_id':idea.id, 'next':reverse('idea:idea_detail', args=(idea.id,))})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(idea.vote_set.all()), 0)

        #Check to see that the button on page displays Like option
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertContains(resp, 'value="Like" id="vote_up"', status_code=200, html=False)

    def test_must_logged_in(self):
        """ 
            A user must be logged in to vote. 
        """
        idea = models.Idea(creator=random_user(), title='Transit subsidy to Mars', 
                    text='Aliens need assistance.', state=self.state)
        idea.save()
        resp = self.client.post(reverse('idea:upvote_idea'), {'idea_id':idea.id, 'next':reverse('idea:idea_detail', args=(idea.id,))})
        self.assertIn('up', resp['Location'])
