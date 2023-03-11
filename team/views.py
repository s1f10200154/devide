from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt
import urllib
import json
import random

from .models import Reply

WEBHOOK_URL = 'https://hooks.slack.com/services/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'
VERIFICATION_TOKEN = 'uIFr66VMZbTPZaYwmDuV1Qhn'
ACTION_HOW_ARE_YOU = 'HOW_ARE_YOU'

def index(request):
    positive_replies = Reply.objects.filter(response=Reply.POSITIVE)
    neutral_replies = Reply.objects.filter(response=Reply.NEUTRAL)
    negative_replies = Reply.objects.filter(response=Reply.NEGATIVE)

    context = {
        'positive_replies': positive_replies,
        'neutral_replies': neutral_replies,
        'negative_replies': negative_replies,

    }
    return render(request, 'index.html', context)

def clear(request):
    Reply.objects.all().delete()
    return redirect(index)

def announce(request):
    if request.method == 'POST':
        data = {
            'text': request.POST['message']
        }
        post_message(WEBHOOK_URL, data)

    return redirect(index)

@csrf_exempt
def echo(request):
    if request.method != 'POST':
        return JsonResponse({})
    
    if request.POST.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    user_name = request.POST['user_name']
    user_id = request.POST['user_id']
    content = request.POST['text']

    result = {
        'text': '<@{}> {}'.format(user_id, content.upper()),
        'response_type': 'in_channel'
    }

    return JsonResponse(result)

@csrf_exempt
def hello(request):
    if request.method != 'POST':
        return JsonResponse({result})
    
    if request.POST.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    user_name = request.POST['user_name']
    user_id = request.POST['user_id']
    content = request.POST['text']

    result = {
        'blocks': [
            {
                'type' : 'section',
                'text' : {
                    'type': 'mrkdwn',
                    'text': '<@{}> Let\'s janken!!'.format(user_id)
                },
                'accessory': {
                    'type': 'static_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'I am:',
                        'emoji': True
                    },
                    'options': [
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': ':fist:',
                                'emoji': True
                            },
                            'value': 'fist'
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': ':v:',
                                'emoji': True
                            },
                            'value': 'v'
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': ':raised_hand_with_fingers_splayed:',
                                'emoji': True
                            },
                            'value': 'raised_hand_with_fingers_splayed'
                        }
                    ],
                    'action_id': ACTION_HOW_ARE_YOU
                }
            }
        ],
        'response_type': 'in_channel'
    }

    return JsonResponse(result)

@csrf_exempt
def reply(request):

    if request.method != 'POST':
        return JsonResponse({})
    
    payload = json.loads(request.POST.get('payload'))
    print(payload)
    if payload.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    if payload['actions'][0]['action_id'] != ACTION_HOW_ARE_YOU:
        raise SuspiciousOperation('Invalid request.')
    
    user = payload['user']
    selected_value = payload['actions'][0]['selected_option']['value']
    response_url = payload['response_url']

    x = ['fist','V','hand']

    if selected_value == 'fist':
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.POSITIVE)
        reply.save()
        y = random.choice(x)
        if y == 'fist':
            response = {
            'text': '<@{}> :fist: Draw.'.format(user['id'])
            }
        elif y == 'hand':
            response = {
            'text': '<@{}> :raised_hand_with_fingers_splayed: You lose.'.format(user['id'])
            }
        else:
            response = {
            'text': '<@{}> :v: You win.'.format(user['id'])
            }

        
    elif selected_value == 'v':
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.NEGATIVE)
        reply.save()
        y = random.choice(x)
        if y == 'fist':
            response = {
            'text': '<@{}> :fist: You lose.'.format(user['id'])
            }
        elif y == 'hand':
            response = {
            'text': '<@{}> :raised_hand_with_fingers_splayed: You win.'.format(user['id'])
            }
        else:
            response = {
            'text': '<@{}> :v: Draw.'.format(user['id'])
            }


    else:
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.NEUTRAL)
        reply.save()
        y = random.choice(x)
        if y == 'fist':
            response = {
            'text': '<@{}> :fist: You win.'.format(user['id'])
            }
        elif y == 'hand':
            response = {
            'text': '<@{}> :raised_hand_with_fingers_splayed: Draw.'.format(user['id'])
            }
        else:
            response = {
            'text': '<@{}> :v: You lose.'.format(user['id'])
            }
    
    post_message(response_url, response)
    return JsonResponse({})
def post_message(url, data):
    headers = {
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()