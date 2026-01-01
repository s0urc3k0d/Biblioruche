#!/usr/bin/env python3
# Test script to debug vote display issues

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import VotingSession, VoteOption, Vote, User
from datetime import datetime

app = create_app()

with app.app_context():
    print("=== DEBUG: VotingSession data ===")
    
    # Check if vote 2 exists
    vote_2 = VotingSession.query.get(2)
    if not vote_2:
        print("❌ Vote ID 2 does not exist!")
        # Show all votes
        all_votes = VotingSession.query.all()
        print(f"Available votes: {[v.id for v in all_votes]}")
        for v in all_votes:
            print(f"  Vote {v.id}: {v.title} - Status: {v.status}")
    else:
        print(f"✅ Vote 2 exists: {vote_2.title}")
        print(f"  Status: {vote_2.status}")
        print(f"  End date: {vote_2.end_date}")
        print(f"  End date type: {type(vote_2.end_date)}")
        
        # Check options (books)
        print(f"\n=== Books in vote 2 ===")
        books = vote_2.books  # This should be VoteOption objects
        print(f"Number of options: {len(books)}")
        
        for i, option in enumerate(books):
            print(f"  Option {i+1}:")
            print(f"    Type: {type(option)}")
            print(f"    ID: {option.id}")
            try:
                print(f"    Book: {option.book.title} by {option.book.author}")
            except Exception as e:
                print(f"    ❌ Error accessing book: {e}")
        
        # Check votes
        print(f"\n=== Votes for session 2 ===")
        votes = Vote.query.filter_by(voting_session_id=2).all()
        print(f"Total votes: {len(votes)}")
        
        # Test vote count method
        for option in books:
            try:
                count = option.get_vote_count()
                print(f"  {option.book.title}: {count} votes")
            except Exception as e:
                print(f"  ❌ Error getting vote count for option {option.id}: {e}")
