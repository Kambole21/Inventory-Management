from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from flask import Flask
from app import db  

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('','Select a role'),('normal', 'Normal'), ('admin', 'Staff')])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=9, max=13)])
    student_number = StringField('Student Number')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    con_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    reg_button = SubmitField('Create Account')

    def validate_email(self, field):
        # Check if email already exists in the database
        if db.user_collection.find_one({'email': field.data}):
            raise ValidationError('This email is already registered. Please use a different email.')

    def validate_student_number(self, field):
        if self.role.data == 'normal' and not field.data:
            raise ValidationError('Student number is required for Normal User.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    sub_button = SubmitField('Sign in')

class ResetPassword(FlaskForm):
    new_password = PasswordField('Enter New Password', validators=[DataRequired(), Length(min=4)])
    con_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Submit')

class ResetEmail(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Email')