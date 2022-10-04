

from abc import ABC

from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, ParseMode, ReplyKeyboardRemove
from mr_knowledge_bot.bot.conversations.telegram.conversation import Conversation
from mr_knowledge_bot.bot.services import MovieService


class TelegramMovieConversation(Conversation, ABC):
    (
        query_movie_for_overview_stage,
        display_movie_overview_stage,
        query_movie_for_trailer_stage,
        display_movie_trailer_stage
    ) = range(4)

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self._movie_service = MovieService.from_context(context=context)

    def find_movies_by_name_command(
        self, name: str, limit: int, sort_by: str
    ):
        chat_id = self._update.message.chat_id
        self._context.bot.send_message(chat_id, text=self.hang_on_message)

        movies = self._movie_service.find_by_name(movie_name=name, limit=limit, sort_by=sort_by)
        return self.display_movies(movies)

    def discover_movies_command(
        self,
        limit: int,
        sort_by: str = None,
        before_date: str = None,
        after_date: str = None,
        with_genres: str = None,
        without_genres: str = None,
        before_runtime: str = None,
        after_runtime: str = None,
        not_released: bool = None
    ):
        chat_id = self._update.message.chat_id
        self._context.bot.send_message(chat_id, text=self.hang_on_message)

        movies = self._movie_service.discover(
            limit=limit,
            sort_by=sort_by,
            before_date=before_date,
            after_date=after_date,
            with_genres=with_genres,
            without_genres=without_genres,
            before_runtime=before_runtime,
            after_runtime=after_runtime,
            not_released=not_released
        )

        return self.display_movies(movies)

    def display_movies(self, movies):
        if movies:
            self._context.user_data['movies'] = movies  # save the found movies for next stages in the conversation.
            movie_names = '\n'.join([movie.name for movie in movies])
            self._update.effective_message.reply_text(
                text=f'Found the following movies for you 😀\n\n{movie_names}',
                reply_to_message_id=self._update.message.message_id
            )
            next_stage = self.yes_or_no_movie_overview()
        else:
            self._update.effective_message.reply_text(
                text=f'Could not find any movies for you 😞',
                reply_to_message_id=self._update.message.message_id
            )
            next_stage = ConversationHandler.END

        return next_stage

    def yes_or_no_movie_overview(self):
        self._context.bot.send_message(
            chat_id=self.get_chat_id(),
            text='Would you like to see an overview of one of the movies?',
            reply_markup=self.get_yes_or_no_keyboard()
        )

        return self.query_movie_for_overview_stage

    def choose_movie(self, answer):
        if answer == 'n':  # user does not want to see movie overview
            return None
        # user wants to see the movie overview
        return ReplyKeyboardMarkup.from_column(
            [movie.name for movie in self._movie_service.movies], resize_keyboard=True, one_time_keyboard=True
        )

    def query_movie_overview(self):
        if movies_to_choose := self.choose_movie(self._update.callback_query.data):
            text = 'Please choose a movie from the list to get its overview.'
            self._context.bot.send_message(
                text=text, reply_markup=movies_to_choose, chat_id=self._update.callback_query.message.chat_id
            )
            next_stage = self.display_movie_overview_stage
        else:
            next_stage = self.yes_or_no_movie_trailer()

        return next_stage

    def display_movie_overview(self):
        chosen_movie = self._update.message.text
        if movie_overview := self._movie_service.get_movie_overview(chosen_movie=chosen_movie):
            self._update.effective_message.reply_text(
                text=f'{chosen_movie} - (Overview)\n\n{movie_overview}',
                reply_to_message_id=self._update.message.message_id,
                reply_markup=ReplyKeyboardRemove()
            )
            next_stage = self.yes_or_no_movie_trailer()
        else:
            self._update.effective_message.reply_text(
                text='I could not understand which movie you meant 🤔, please choose again from the list.',
                reply_to_message_id=self._update.message.message_id
            )
            next_stage = self.display_movie_overview_stage
        return next_stage

    def yes_or_no_movie_trailer(self):
        self._context.bot.send_message(
            text='Would you like to view a trailer for one of the movies?',
            reply_markup=self.get_yes_or_no_keyboard(),
            chat_id=self.get_chat_id()
        )
        return self.query_movie_for_trailer_stage

    def query_movie_trailer(self):
        if movies_to_choose := self.choose_movie(self._update.callback_query.data):
            text = 'Please choose a movie from the list to get its trailer.'
            self._context.bot.send_message(
                text=text, reply_markup=movies_to_choose, chat_id=self._update.callback_query.message.chat_id
            )
            next_stage = self.display_movie_trailer_stage
        else:
            next_stage = ConversationHandler.END

        return next_stage

    def display_movie_trailer(self):
        chosen_movie_name = self._update.message.text
        movie_trailer = self._movie_service.get_trailer(chosen_movie_name)
        if movie_trailer:
            self._update.effective_message.reply_text(
                text=f'[{chosen_movie_name} - (Trailer)]({movie_trailer})',
                reply_to_message_id=self._update.message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
            next_stage = ConversationHandler.END
        elif movie_trailer is None:
            self._update.effective_message.reply_text(
                text='I could not understand which movie you meant 🤔, please choose again from the list.',
                reply_to_message_id=self._update.message.message_id,
                reply_markup=ReplyKeyboardRemove()
            )
            next_stage = self.display_movie_trailer_stage
        else:  # movie_trailer = '' - could not find a video
            self._update.effective_message.reply_text(
                text=f'Could not find trailer for movie "{chosen_movie_name}"',
                reply_to_message_id=self._update.message.message_id,
                reply_markup=ReplyKeyboardRemove()
            )
            next_stage = ConversationHandler.END

        return next_stage