"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()
            User.query.delete()
            Message.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)

            db.session.commit()
            self.uid1 = self.testuser.id

    def tearDown(self):
        """drop all and rollback. """

        with app.app_context():
            
            db.session.rollback()
            

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    testuser = db.session.get(User, self.uid1)
                    sess[CURR_USER_KEY] = self.testuser.id

                # Now, that session setting is saved, so we can have
                # the rest of ours test

                resp = c.post("/messages/new", data={"text": "Hello"})

                # Make sure it redirects
                self.assertEqual(resp.status_code, 302)

                msg = Message.query.one()
                self.assertEqual(msg.text, "Hello")

    def test_render_add_message(self):
        """does get request to endpoint render form and template appropriately?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    testuser = db.session.get(User, self.uid1)
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.get("/messages/new")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('data="rendered-new-message-form"', html)

    def test_show_message(self):
        """signed in user should see message from message_id."""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    testuser = db.session.get(User, self.uid1)
                    sess[CURR_USER_KEY] = self.testuser.id
                m = Message(text="test warble",
                            user_id=self.uid1)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()
                m = Message.query.filter(Message.id == mid).first()

                resp = c.get(f'/messages/{m.id}')
                html = resp.get_data(as_text=True)
                # print('html is ', html)
                self.assertEqual(resp.status_code, 200)
                self.assertIn('action="/messages/1111/delete">', html)
                self.assertIn('<p class="single-message">test warble</p>', html, "not contained")

    def test_disallow_show_message_for_unauthorized(self):
        """anonymous user cannot see message. Should detect redirect on second round."""

        with app.app_context():
            with self.client as c:
                m = Message(text="test warble",
                            user_id=self.uid1)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()
                m = Message.query.filter(Message.id == mid).first()

                resp = c.get(f'/messages/{m.id}')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 302)

    def test_disallow_show_message_for_unauthorized(self):
        """anonymous user cannot see message. Should detect redirect."""

        with app.app_context():
            with self.client as c:
                m = Message(text="test warble",
                            user_id=self.uid1)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()
                m = Message.query.filter(Message.id == mid).first()

                resp = c.get(f'/messages/{m.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)
                
                self.assertEqual(resp.status_code, 200)
                self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
                self.assertIn("Access unauthorized", html)

    def test_delete_message_with_auth(self):
        """user can delete their own message if they're logged in."""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                m = Message(text="test warble",
                            user_id=self.uid1)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()

                m = Message.query.filter(Message.id == mid).first()

                resp = c.post(f"/messages/{mid}/delete", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Message deleted!", html)

    def test_delete_message_without_auth(self):
        """can user delete message if not signed in/authenticated?"""

        with app.app_context():
            with self.client as c:
                m = Message(text="test warble",
                            user_id=self.uid1)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()

                m = Message.query.filter(Message.id == mid).first()

                resp = c.post(f"/messages/{mid}/delete", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized.", html)

    def test_delete_message_from_different_user(self):
        """Can a logged in user delete another users message?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u = User.signup("test2", "test2@email.com", "password", None)
                uid2 = 2222
                u.id = uid2
                db.session.add(u)
                db.session.commit()

                m = Message(text="test warble",
                            user_id=uid2)
                mid = 1111
                m.id = mid
                db.session.add(m)
                db.session.commit()

                m = Message.query.filter(Message.id == mid).first()

                resp = c.post(f"/messages/{mid}/delete", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("You cannot delete a message from a different user!", html)