"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()


class UserModelTestCase(TestCase):
    """Test User Model"""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u3 = User.signup("test3", "test3@email.com", "password", None)
            uid3 = 3333
            u3.id = uid3

            u4 = User.signup("test4", "test4@email.com", "password", None)
            uid4 = 4444
            u4.id = uid4

            db.session.commit()

            u3 = db.session.get(User, uid3)
            u4 = db.session.get(User, uid4)

            self.u3 = u3
            self.uid3 = uid3

            self.u4 = u4
            self.uid4 = uid4

            self.client = app.test_client()


    def tearDown(self):
        """Empty query and tear down and remove """
        
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            return res

    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u3 = db.session.get(User, 3333)
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
            print("self.u3 is ", self.u3)
            db.session.add(u)
            db.session.commit()
            print('u from single function instance is ', u)
            print("after 'db.session.commit()', self.u3 is ", self.u3)
            # User should have no messages & no followers
            self.assertEqual(len(self.u3.messages), 0)
            self.assertEqual(len(self.u3.followers), 0)
            
            # tests for setup instance of users due to context and persistance (and detached parents) issues
            self.assertEqual(len(self.u3.messages), 0)
            self.assertEqual(self.u3.id, 3333)

            self.assertEqual(self.u3.__repr__(), "<User #3333: test3, test3@email.com>")

    def test_user_signup_password_failure(self):
        """does .signup fail without proper password"""

        with app.app_context():
            self.assertRaises(ValueError, lambda: User.signup("test1", "testemail.com", None, None))
            
    def test_user_signup_email_failure(self):
        """does .signup fail without proper email"""

        with app.app_context():
            u1 = User.signup("test1", None, "password", None)
            uid1 = 1111
            u1.id = uid1
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()

    def test_user_signup_username_failure(self):
        """does .signup fail without proper username"""

        with app.app_context():
            u1 = User.signup(None, "test1@email.com", "password", None)
            uid1 = 1111
            u1.id = uid1
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
    
    def test_user_follows(self):
        """Do methods 'is_following' and 'is_followed_by' work correctly?"""
            
        with app.app_context():
            u1 = User.signup("test1", "test1@email.com", "password", None)
            u2 = User.signup("test2", "test2@email.com", "password", None)
            db.session.add_all([u1, u2])
            db.session.commit()

            self.assertFalse(u1.is_followed_by(u2))
            self.assertFalse(u1.is_following(u2))
            
            u1.following.append(u2)
            db.session.commit()
            
            self.assertEqual(len(u2.followers), 1)
            self.assertEqual(len(u1.followers), 0)
            self.assertEqual(len(u2.following), 0)
            self.assertEqual(len(u1.following), 1)

            self.assertFalse(u1.is_followed_by(u2))
            self.assertTrue(u1.is_following(u2))

    def test_authenticate(self):
        """Does class method authenticate with the proper credentials?"""

        with app.app_context():
            u1 = User.signup("test1", "test1@email.com", "password", None)
            db.session.add(u1)
            db.session.commit()

            self.assertEqual(User.authenticate("test1", "password"), u1)
            self.assertFalse(User.authenticate("test1", "wrongPassword"))
            self.assertFalse(User.authenticate("wronguser", "password"))

    def test_model_attributes(self):
        """Does a User record contain the appropriate defaults?"""

        with app.app_context():
            u1 = User.signup("test1", "test1@email.com", "password", None)
            db.session.add(u1)
            db.session.commit()

            self.assertEqual(u1.header_image_url, "/static/images/warbler-hero.jpg")