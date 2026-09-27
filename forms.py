from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, HiddenField, IntegerField, SelectField
from wtforms.validators import InputRequired, EqualTo, NumberRange, DataRequired

class RegistrationForm(FlaskForm):
    user_id = StringField("User_id: ",
                          validators=[InputRequired()])
    password = PasswordField("Password: ",
                             validators=[InputRequired()])
    password2 = PasswordField("Confirm Password: ",
                              validators=[InputRequired(),
                                          EqualTo("password")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    user_id = StringField("User id: ",
                          validators=[InputRequired()])
    password = PasswordField("Password: ",
                             validators=[InputRequired()])
    submit = SubmitField("Login")

class AddBootForm(FlaskForm):
    boot_name = StringField("Name of boot: ",
                            validators=[InputRequired()])
    price = IntegerField("Price: ",
                         validators=[InputRequired()])
    description = StringField("Description: ",
                              validators=[InputRequired()])
    image = FileField("Upload image: ",
                      validators=[DataRequired()])
    submit = SubmitField()

class EditBootForm(FlaskForm):
    boot_name = StringField("Name of boot: ",
                        validators=[InputRequired()])
    price = IntegerField("Price: ",
                         validators=[InputRequired()])
    description = StringField("Description: ",
                              validators=[InputRequired()])
    
    submit = SubmitField()



class ReviewForm(FlaskForm):
    boot_id = HiddenField("Boot ID")
    rating = IntegerField("Rating: ", 
                          validators=[InputRequired(),
                                      NumberRange(0, 5)])
    review = StringField("Review: ", validators=[InputRequired()])
    submit = SubmitField("Submit review")


class CheckoutForm(FlaskForm):
    first_name = StringField("first name:",
                             validators=[InputRequired()])
    last_name = StringField("Last name",
                            validators=[InputRequired()])
    address = StringField("Address: ",
                          validators=[InputRequired()])
    payment_method = SelectField("payment method: ", choices=["Debit Card", "Credit Card", 
                                                              "Paypal", "Venmo",
                                                              "Bitcoin"])

    submit = SubmitField("Confirm Purchase")