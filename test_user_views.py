"""User View tests."""

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

class UserViewTestCase(TestCase):
    """Test views for users."""

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

    def test_signup(self):
        """Should render form at GET request for user to signup."""

        with app.app_context():
            with self.client as c:
                resp = c.get('/signup')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('id="user_form"', html)

    def test_signup_form_submit(self):
        """Does signup form submission add user and redirect?"""

        with app.app_context():
            with self.client as c:
                d = {'username' : 'testuser2',
                     'email' : 'testuser2@email.com',
                     'password' : 'password',
                     'image_url' : None 
                     }
                
                resp = c.post('/signup', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Successfully created account', html)

    def test_signup_form_submission_failure(self):
        """Does form submission fail if credentials are not met and re-render form?"""

        with app.app_context():
            with self.client as c:
                d = {'username' : 'testuser',
                     'email' : 'testuser2@email.com',
                     'password' : 'password',
                     'image_url' : None 
                     }
                
                resp = c.post('/signup', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Username already taken', html)
                self.assertIn('id="user_form"', html)

    def test_login_get(self):
        """Does route load login form before submission"""

        with app.app_context():
            with self.client as c:
                resp = c.get("/login")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('id="user_form"', html)
                self.assertIn('<button class="btn btn-primary btn-block btn-lg">Log in</button>', html)

    def test_login_submission(self):
        """does login form authenticate user appropriately?"""

        with app.app_context():
            with self.client as c:
                d = {"username" : "testuser",
                     "password" : "testuser"}
                
                resp = c.post('/login', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Hello, testuser", html)

    def test_login_submission_failure(self):
        """does login form disallow authenticate with wrong credentials?"""

        with app.app_context():
            with self.client as c:
                d = {"username" : "wronguser",
                     "password" : "testuser"}
                
                resp = c.post('/login', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Invalid credentials.", html)

        with app.app_context():
            with self.client as c:
                d = {"username" : "testuser",
                     "password" : "wrongpassword"}
                
                resp = c.post('/login', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Invalid credentials.", html)

    def test_logout_submission(self):
        """does endpoint log user out and redirect?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                resp = c.get('/logout', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Successfully logged out! See you soon!", html)

    def test_show_users(self):
        """Does search show users from query"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                u3 = User.signup("testuser3", "test3@email.com", "password", None)
                u4 = User.signup("testuser4", "test4@email.com", "password", None)
                u5 = User.signup("testuser5", "test5@email.com", "password", None)

                db.session.add_all([u2, u3, u4, u5])
                db.session.commit()

                resp = c.get('/users')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<a href="/users/2" class="card-link">', html)
                self.assertIn('<a href="/users/3" class="card-link">', html)
                self.assertIn('<a href="/users/4" class="card-link">', html)
                self.assertIn('<a href="/users/5" class="card-link">', html)

    def test_show_users_with_q(self):
        """Does search return queried user if exists?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                
                u2 = User.signup("testuser2", "test2@email.com", "password", None)

                db.session.add(u2)
                db.session.commit()

                resp = c.get('/users', query_string={'q': "testuser2"})
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<a href="/users/2" class="card-link">', html)

    def test_show_no_users_with_q(self):
        """Does search return no users message if none exist?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.get('/users', query_string={'q': "testuser2"})
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<h3>Sorry, no users found</h3>', html)

    def test_show_user_profile(self):
        """Does it show a proper user profile for the given id?"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                m1 = Message(text="warble",
                             user_id=self.testuser.id)
                
                m2 = Message(text="warble2",
                             user_id=self.testuser.id)
                
                m3 = Message(text="warble3",
                             user_id=self.testuser.id)
                
                db.session.add_all([m1, m2, m3])
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('data="data-contained-1"', html)
                self.assertIn('data="data-contained-2"', html)
                self.assertIn('data="data-contained-3"', html)

    def test_show_user_following(self):
        """Does route show which users current user is following if user authenticated"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                u3 = User.signup("testuser3", "test3@email.com", "password", None)

                db.session.add_all([u2, u3])
                db.session.commit()

                u1 = db.session.get(User, self.uid1)

                u1.following.append(u2)
                u1.following.append(u3)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/following')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'<a href="/users/{u2.id}" class="card-link">', html)
                self.assertIn(f'<a href="/users/{u3.id}" class="card-link">', html)

    def test_show_user_following_without_authenticate(self):
        """route should disallow viewing and flash error message"""

        with app.app_context():
            with self.client as c:
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                u3 = User.signup("testuser3", "test3@email.com", "password", None)

                db.session.add_all([u2, u3])
                db.session.commit()

                u1 = db.session.get(User, self.uid1)

                u1.following.append(u2)
                u1.following.append(u3)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access to route: following is unauthorized without login', html)
                

    def test_show_user_followers(self):
        """route should show followers of logged in user"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                u3 = User.signup("testuser3", "test3@email.com", "password", None)

                db.session.add_all([u2, u3])
                db.session.commit()

                u1 = db.session.get(User, self.uid1)
                
                u1.followers.append(u2)
                u1.followers.append(u3)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/followers')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'<a href="/users/{u2.id}" class="card-link">', html)
                self.assertIn(f'<a href="/users/{u3.id}" class="card-link">', html)

    def test_show_user_followers_without_auth(self):
        """route should disallow show followers and flash error message"""

        with app.app_context():
            with self.client as c:

                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                u3 = User.signup("testuser3", "test3@email.com", "password", None)

                db.session.add_all([u2, u3])
                db.session.commit()

                u1 = db.session.get(User, self.uid1)
                
                u1.followers.append(u2)
                u1.followers.append(u3)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access to route: followers is unauthorized without login', html)
                
    def test_user_add_follow(self):
        """Route should add follow of selected user_id"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u2 = User.signup("testuser2", "test2@email.com", "password", None)

                db.session.add(u2)
                db.session.commit()
                
                resp = c.post(f'/users/follow/{u2.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'You are now following {u2.username}', html)

    def test_user_add_follow_without_auth(self):
        """Route should disallow add and redirect to main and flash error"""

        with app.app_context():
            with self.client as c:
                u2 = User.signup("testuser2", "test2@email.com", "password", None)

                db.session.add(u2)
                db.session.commit()
                
                resp = c.post(f'/users/follow/{u2.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access to add follow is unauthorized without login', html)

    def test_user_stop_following_with_auth(self):
        """Route should remove follow and flash success message"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()

                u1 = User.query.filter(User.id == self.uid1).first()

                u1.following.append(u2)
                db.session.commit()

                resp = c.post(f'/users/stop-following/{u2.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Successfully stopped following user', html)

    def test_user_stop_following_without_auth(self):
        """Route should remove follow and flash success message"""

        with app.app_context():
            with self.client as c:
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()

                u1 = User.query.filter(User.id == self.uid1).first()

                u1.following.append(u2)
                db.session.commit()

                resp = c.post(f'/users/stop-following/{u2.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Access to stop-following is unauthorized without login', html)

    def test_user_profile_get_edit(self):
        """Route should render form so a user can edit profile."""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.get('/users/profile')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)
                self.assertIn('<form method="POST" id="user_form">', html)

    def test_user_profile_post_edit(self):
        """Route should pull form data so a user can edit profile."""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u = db.session.get(User, self.uid1)
                d = {
                    "username" : "editedusername",
                    "email" : "editedemail",
                    "image_url" : "edited_image.jpeg",
                    "bio" : "editedbio",
                    "header_image_url" : None,
                    "password" : "testuser"
                }

                resp = c.post('/users/profile', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                u = db.session.get(User, self.uid1)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Successfully updated user information", html)
                self.assertEqual(u.username, "editedusername")
                self.assertEqual(u.email, "editedemail")
                self.assertEqual(u.bio, "editedbio")
                self.assertEqual(u.image_url, "edited_image.jpeg")

    def test_user_profile_without_auth(self):
        """Route should redirect with error message"""

        with app.app_context():
            with self.client as c:
                u = db.session.get(User, self.uid1)
                d = {
                    "username" : "editedusername",
                    "email" : "editedemail",
                    "image_url" : "edited_image.jpeg",
                    "bio" : "editedbio",
                    "header_image_url" : None,
                    "password" : "testuser"
                }

                resp = c.post('/users/profile', data=d, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Unauthorized. Cannot edit user profile. Please login!", html)

    def test_user_delete_with_auth(self):
        """Does route delete user"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                
                resp = c.post('/users/delete', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("User delete. We hope to see you again!", html)

    def test_user_delete_with_auth(self):
        """Does route delete user"""

        with app.app_context():
            with self.client as c:
                
                resp = c.post('/users/delete', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Unauthorized action. Cannot delete user without user login", html)

    def test_toggle_like_add_with_auth(self):
        """route should add target like and flash success message"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()
                m1 = Message(text="warble",
                             user_id=u2.id)
                db.session.add(m1)
                db.session.commit()

                resp = c.post(f'/users/toggle_like/{m1.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Message liked", html)

    def test_toggle_like_remove_with_auth(self):
        """route should add target like and flash success message"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u1 = db.session.get(User, self.testuser.id)
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()
                m1 = Message(text="warble",
                             user_id=u2.id)
                db.session.add(m1)
                db.session.commit()
                u1.likes.append(m1)
                db.session.commit()

                resp = c.post(f'/users/toggle_like/{m1.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Message removed from likes", html)

    def test_toggle_like_owned_message_with_auth(self):
        """route should add target like and flash success message"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                m1 = Message(text="warble",
                             user_id=self.testuser.id)
                db.session.add(m1)
                db.session.commit()

                resp = c.post(f'/users/toggle_like/{m1.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Sorry! You cannot like your own message", html)

    def test_toggle_like_without_auth(self):
        """Should disallow liking message and redirect with flash error"""

        with app.app_context():
            with self.client as c:

                m1 = Message(text="warble",
                             user_id=self.testuser.id)
                db.session.add(m1)
                db.session.commit()

                resp = c.post(f'/users/toggle_like/{m1.id}', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized. Must be logged in to like messages", html)

    def test_show_user_likes_with_auth(self):
        """should direct to view page showing users likes instead of users messages"""

        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id
                u1 = db.session.get(User, self.uid1)
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()
                m1 = Message(text="warble",
                             user_id=u2.id)
                db.session.add(m1)
                db.session.commit()
                u1.likes.append(m1)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/likes')
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'data="data-contained-{m1.id}"', html)

    def test_show_user_likes_without_auth(self):
        """should redirect to main and flash error"""

        with app.app_context():
            with self.client as c:
                u1 = db.session.get(User, self.uid1)
                u2 = User.signup("testuser2", "test2@email.com", "password", None)
                db.session.add(u2)
                db.session.commit()
                m1 = Message(text="warble",
                             user_id=u2.id)
                db.session.add(m1)
                db.session.commit()
                u1.likes.append(m1)
                db.session.commit()

                resp = c.get(f'/users/{self.testuser.id}/likes', follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Unauthorized. Must be logged in to view likes.", html)