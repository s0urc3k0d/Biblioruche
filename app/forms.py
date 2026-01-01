from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateTimeField, DateField, SelectField, RadioField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import TextArea

class BookProposalForm(FlaskForm):
    title = StringField('Titre du livre', validators=[DataRequired(), Length(min=1, max=200)])
    author = StringField('Auteur', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    publisher = StringField('Éditeur', validators=[Optional(), Length(max=100)])
    publication_year = IntegerField('Année de publication', validators=[Optional(), NumberRange(min=1000, max=2030)])
    pages_count = IntegerField('Nombre de pages', validators=[Optional(), NumberRange(min=1, max=10000)])
    genre = StringField('Genre', validators=[Optional(), Length(max=100)])

class ReadingSessionForm(FlaskForm):
    book_id = SelectField('Livre sélectionné', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    
    # Option pour ajouter un nouveau livre
    add_new_book = BooleanField('Ajouter un nouveau livre')
    new_book_title = StringField('Titre du nouveau livre', validators=[Optional(), Length(min=1, max=200)])
    new_book_author = StringField('Auteur du nouveau livre', validators=[Optional(), Length(min=1, max=200)])
    new_book_description = TextAreaField('Description du nouveau livre', validators=[Optional(), Length(max=1000)])
    new_book_isbn = StringField('ISBN du nouveau livre', validators=[Optional(), Length(max=20)])
    new_book_publisher = StringField('Éditeur du nouveau livre', validators=[Optional(), Length(max=100)])
    new_book_publication_year = IntegerField('Année de publication du nouveau livre', validators=[Optional(), NumberRange(min=1000, max=2030)])
    new_book_pages_count = IntegerField('Nombre de pages du nouveau livre', validators=[Optional(), NumberRange(min=1, max=10000)])
    new_book_genre = StringField('Genre du nouveau livre', validators=[Optional(), Length(max=100)])
    
    start_date = DateField('Date de début', validators=[DataRequired()])
    end_date = DateField('Date de fin', validators=[DataRequired()])
    debrief_date = DateField('Date du live de débrief', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])

class VotingSessionForm(FlaskForm):
    title = StringField('Titre du vote', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    end_date = DateField('Date de fin du vote', validators=[DataRequired()])

class VoteForm(FlaskForm):
    vote_option_ids = SelectMultipleField('Vos choix', coerce=int, validators=[DataRequired()])

class EditVotingSessionForm(FlaskForm):
    title = StringField('Titre du vote', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    end_date = DateField('Date de fin du vote', validators=[DataRequired()])

class EditReadingSessionForm(FlaskForm):
    start_date = DateField('Date de début', validators=[DataRequired()])
    end_date = DateField('Date de fin', validators=[DataRequired()])
    debrief_date = DateField('Date du live de débrief', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])

class BookReviewForm(FlaskForm):
    rating = RadioField('Votre note', 
                       choices=[('1', '1 étoile'), ('2', '2 étoiles'), ('3', '3 étoiles'), 
                               ('4', '4 étoiles'), ('5', '5 étoiles')],
                       validators=[DataRequired()], coerce=int)
    comment = TextAreaField('Votre avis', validators=[Optional(), Length(max=1000)],
                           render_kw={"placeholder": "Partagez votre avis sur ce livre..."})

class ModerateReviewForm(FlaskForm):
    is_visible = BooleanField('Avis visible')
    is_moderated = BooleanField('Avis modéré')