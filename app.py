import streamlit as st
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('Databas')

def save_entry_to_dynamodb(text):
    now = datetime.now()
    week = now.isocalendar()[1]
    entry = {
        'id': str(uuid.uuid4()),
        'week': week,
        'text': text,
        'timestamp': now.isoformat()
    }
    table.put_item(Item=entry)

def get_entries_by_week(week):
    response = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('week').eq(week))
    return response['Items']


def update_entry_in_dynamodb(entry_id, new_text):
    now = datetime.now()
    table.update_item(
        Key={'id': entry_id},
        UpdateExpression='SET text = :new_text, timestamp = :new_timestamp',
        ExpressionAttributeValues={
            ':new_text': new_text,
            ':new_timestamp': now.isoformat()
        }
    )

def delete_entry_from_dynamodb(entry_id):
    table.delete_item(Key={'id': entry_id})

current_week = datetime.now().isocalendar()[1]

if 'selected_week' not in st.session_state:
    st.session_state.selected_week = current_week

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None

st.title("Igor's Dagbok")

new_entry = st.text_area(" ", placeholder="Skriv ett nytt inlägg här...")
if st.button("Spara inlägg"):
    if new_entry.strip():
        save_entry_to_dynamodb(new_entry.strip())
        st.success("Inlägg sparat!")

st.header("Visa inlägg för vecka")

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️"):
        if st.session_state.selected_week > 1:
            st.session_state.selected_week -= 1
with col3:
    if st.button("➡️"):
        if st.session_state.selected_week < 53:
            st.session_state.selected_week += 1
with col2:
    st.markdown(f"<h2 style='text-align: center;'>Vecka {st.session_state.selected_week}</h2>", unsafe_allow_html=True)

entries = get_entries_by_week(st.session_state.selected_week)

if entries:
    st.subheader(f"Inlägg från vecka {st.session_state.selected_week}")
    for entry in entries:
        if st.session_state.edit_mode == entry['id']:
            edited_text = st.text_area(f"Redigera inlägg", entry['text'], key=entry['id'])
            if st.button(f"Spara ändringar", key=f"save_{entry['id']}"):
                update_entry_in_dynamodb(entry['id'], edited_text)
                st.session_state.edit_mode = None
            if st.button(f"Avbryt", key=f"cancel_{entry['id']}"):
                st.session_state.edit_mode = None
        else:
            st.write(f"Inlägg från {entry['timestamp']}")
            st.write(entry['text'])
            col4, col5 = st.columns([9, 1])
            with col5:
                if st.button("✏️", key=f"edit_{entry['id']}"):
                    st.session_state.edit_mode = entry['id']
                if st.button("🗑️", key=f"delete_{entry['id']}"):
                    delete_entry_from_dynamodb(entry['id'])
            st.write("---")
else:
    st.info(f"Inga inlägg hittades för vecka {st.session_state.selected_week}.")
