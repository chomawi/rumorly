"""
Reproducing

Zhao, Zhe, Paul Resnick, and Qiaozhu Mei. "Enquiring minds: Early
detection of rumors in social media from enquiry posts." Proceedings of
the 24th International Conference on World Wide Web. ACM, 2015.

http://dl.acm.org/citation.cfm?id=2741637
"""

import sys
import re
import json
import gzip
from collections import Counter
import random
from random import randint
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH
import networkx as nx

non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
lsh_signal=MinHashLSH(threshold=0.6,num_perm=50)
lsh_non_signal=MinHashLSH(threshold=0.6,num_perm=50)
g=nx.Graph()
all_tweets=[]
signal_tweets=[]
non_signal_tweets=[]
signal_id_text={}
non_signal_id_text={}
signal_minhashes={}
non_signal_minhashes={}


def is_signal_tweet(tweet_text):              
    """
    identifies a tweet as signal or not using the following RegEx
    is (that | this | it) true
    wh[a]*t[?!][?1]*
    ( real? | really ? | unconfirmed )
    (rumor | debunk)
    (that | this | it) is not true
    Args:
    @param(str): input tweet text
    @output: true if the tweet is a signal tweet, false otherwise
    """              
    sentence = (tweet_text.translate(non_bmp_map))
    matches = bool(re.search('(is\s?(that\s?|this\s?|it\s?)true\s?[?]?)|^real$|^reall[y]*[\s]?[?]*$|^unconfirmed$|rumor|debunk|(this\s?|that\s?|it\s?)is\s?not\s?true|wh[a]*[t]*[?!][?]*',sentence,re.IGNORECASE))
    return matches


def minhash(tweet_text,tweet_id,minhashes_dict,lsh_index):   
    """
    Generate a minhash from tweet_text and appends it to dictionary with text as key and appends to lsh index
    Args:
    param1(str): "text" part of the tweet
    param2(dictionary):Dictionary containing the {tweet_text:minhash(tweet_text)} items
    param3(lsh index):LSH Dictionary optimised for a particular treshold which accepts minhash objects
    
    Returns:
    Minhash value of the tweet-text and appends it to the lsh index and minhashes dictionary.
    """
    sentence=(tweet_text.translate(non_bmp_map))
    words = sentence.split(" ")
    m = MinHash(num_perm=50)
    for d in words:
        m.update(d.encode('UTF-8'))
    minhashes_dict.update({tweet_id:m})
    lsh_index.insert("%d"%tweet_id,m)
    return m

def generate_undirected_graph(tweet_id,min_hash):
    """
    An undirected graph of tweets is built by including an edge joining
    any tweet pair with a jaccard similarity of 0.6. Minhash is used to
    efficiently compute the jaccard similarity. The connected components
    in this graph are the clusters.
    
    Args:
    param(dictionary): Dictionary containing {text:minhash} items
        
    Returns:
    Graph, where nodes are tweet_texts and edges are formed between texts if they are similar by value greater than threshold
    
    """
    similar=lsh_signal.query(min_hash)
    g.add_node(tweet_id)
    for each in similar:
        g.add_edge(tweet_id,each)
    return g 

def connected_components(g):  
    """
    From the undirected graph generated by the function-gen_undirected_graph(), 
    the graph is filtered to include only the connected components that include more than the threshold number of nodes
    
    Args:
    param(graph): Graph containing clusters of connected components
    
    Returns:
    Clusters containing more than threshold no of tweets
    
    """
    cconn_comp=sorted(nx.connected_components(g),key=len,reverse=True)
    req_conn_comp=[]
    for each_cluster in conn_comp:
        if (len(each_cluster)>3):
            req_conn_comp.append(each_cluster)
        else:
            pass
    return req_conn_comp

def extract_summary(cluster):  
    """
    For each cluster extracts statement that summarizes the tweets in a signal cluster
    Args:
    param: Set of tweet ids
    
    Returns:
    Most frequent and continuous substrings (3-grams that
    appear in more than 80% of the tweets) in order.
    """
    no_of_tweets=len(cluster)
    req_cutoff=0.8*no_of_tweets
    words_list=[]
    shinglesincluster =[]
    for each_tweet in cluster:
        sente=(each_tweet.translate(non_bmp_map))
        words = sente.split(" ")
        for index in range(0, len(words) - 2):
            shingle = words[index] + " " + words[index + 1] + " " + words[index + 2]
            shinglesincluster.append(shingle)
    tot=dict(Counter(shinglesincluster))
    for k,v in tot.items():
        if v>=req_cutoff:
            words_list.append(k)
    sentence= ' '.join(words_list)
    return sentence
    


def assign_cluster_to_non_signal_tweets(sentence): 
    """
    From a sentence that summarizes each cluster,the sentence is matched against 
    nog-signal tweet_texts to match the tweets that belong to the cluster but donot contain signal patterns
    Args:
    param(str):Statement that summarizes each cluster
    
    Returns:
    Tweet_texts that belong to the cluster
    
    """
    shingles_in_sent=set()
    string=(sentence.translate(non_bmp_map))
    sent_tokens=string.split()
    m=MinHash(num_perm=50)
    for d in sent_tokens:
        m.update(d.encode('UTF-8'))
    similar_nonsignal_tweets=lsh_non_signal.query(m)
    return similar_nonsignal_tweets


def train_classifier():
    false_tweets_ids=[]
    true_tweets_ids=[]
    false_tweets=[]
    true_tweets=[]
    false_signal_tweets=[]
    true_signal_tweets=[]
    for keys,values in train_set.items():
                if values=='false':
                            false_tweets_ids.append(keys)
                elif values=='true':
                           true_tweets_ids.append(keys)
                else:
                            pass
    false_tweets_ids=[int(i) for i in false_tweets_ids]

    true_tweets_ids=[int(i) for i in true_tweets_ids]



    for each_id in false_tweets_ids:
        for each_tweet in tweets:
            if each_id==each_tweet['id']:
                false_tweets.append(each_tweet)
    for each_id in true_tweets_ids:
        for each_tweet in tweets:
            if each_id==each_tweet['id']:
                true_tweets.append(each_tweet)


    for each in false_tweets:
        texts=each['text']
        sentence=(texts.translate(non_bmp_map))
        mat=re.match('(is(that|this|it)true?)|(real|really?|unconfirmed)|(rumor|debunk)|((this|that|it)is not true)|wh[a]*t[?!][?]*',sentence)
        if mat:
            false_signal_tweets.append(each)
        else:
            pass


    for each in true_tweets:
        texts=each['text']
        sentence=(texts.translate(non_bmp_map))
        mat=re.match('(is(that|this|it)true?)|(real|really?|unconfirmed)|(rumor|debunk)|((this|that|it)is not true)|wh[a]*t[?!][?]*',sentence)
        if mat:
            true_signal_tweets.append(each)
        else:
            pass


    def ratio_signal_all(all_tweets,signal_tweets):
        a=len(signal_tweets)
        b=len(all_tweets)
        c=a/b
        return c


    def ratio_entr_word_freq(all_tweets,signal_tweets):
        all_sent=[]
        sig_sent=[]
        for each_tweet in all_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            words=sentence.split(" ")
            all_sent.append(words)
        all_sent=reduce(lambda x,y:x+y,all_sent)
        all_count=Counter(all_sent)
        all_freq=list(all_count.values())
        tot_sum=sum(all_freq)
        for i in range(len(all_freq)):
            all_freq[i]=all_freq[i]/tot_sum
        all_entr=scistat.entropy(all_freq)

        for each_tweet in signal_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            words=sentence.split(" ")
            sig_sent.append(words)
        sig_sent=reduce(lambda x,y: x+y,sig_sent)
        sig_count=Counter(sig_sent)
        sig_freq=list(sig_count.values())
        tot_sig_sum=sum(sig_freq)
        for i in range(len(sig_freq)):
            sig_freq[i]=sig_freq[i]/tot_sig_sum
        sig_entr=scistat.entropy(sig_freq)

        entr=sig_entr/all_entr
        return entr


    def avg_no_words_signal(signal_tweets):
        l=[]
        for each in signal_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            words=sentence.split(" ")
            l.append(len(words))
        return np.mean(l)


    def avg_no_words_alltweets(all_tweets):
        a=avg_no_words_signal(all_tweets)
        return a


    def rat_avg_words(signal_tweets,all_tweets):
        a=avg_no_words_signal(signal_tweets)
        b=avg_no_words_alltweets(all_tweets)
        return (a/b)


    def perc_retweet_signal(signal_tweets):
        signal_retweets=0
        for each in signal_tweets:
            for each_key in each.keys():
                if each_key=='retweeted_status':
                    signal_tweets=signal_retweets+1

        b=(signal_retweets/len(signal_tweets))
        return b

    def perc_retweet_alltweets(all_tweets):
        d=perc_retweet_signal(all_tweets)
        return d


    def avg_urls_signal(signal_tweets):
        url_count=[]
        for each in signal_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            words=sentence.split(" ")
            i=words.count("http:")
            j=words.count("https:")
            k=a+b
            url_count.apend(k)
        return np.mean(url_count)

    def avg_urls_all(all_tweets):
        c=avg_urls_signal(all_tweets)
        return c

    def avg_hashtags_signal_tweet(signal_tweets):
        c=[]
        for each in signal_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            s=re.findall('(?<=^|(?<=[^a-zA-Z0-9-\.]))#([A-Za-z]+[A-Za-z0-9_]+)',sentence)
            no_of_hash=len(s)
            c.append(no_of_hash)
        return np.mean(c)

    def avg_hahstags_all_tweets(all_tweets):
        a=avg_hashtags_signal_tweet(all_tweets)
        return a

    def avg_usernames_signal_tweet(signal_tweets):
        c=[]
        for each in signal_tweets:
            texts=each['text']
            sentence=(texts.translate(non_bmp_map))
            s=re.findall('(?<=^|(?<=[^a-zA-Z0-9-\.]))@([A-Za-z]+[A-Za-z0-9_]+)',sentence)
            no_of_hash=len(s)
            c.append(no_of_hash)
        return np.mean(c)

    def avg_usernames_all_tweets(all_tweets):
        a=avg_usernames_signal_tweet(all_tweets)
        return a

    def statistical_features(all_tweets,signal_tweets):
        f1=ratio_signal_all(all_tweets,signal_tweets)
        f2=ratio_entr_word_freq()
        f3=avg_no_words_signal(signal_tweets)
        f4=avg_no_words_alltweets(all_tweets)
        f5=rat_avg_words(signal_tweets,all_tweets)
        f6=perc_retweet_signal(signal_tweets)
        f7=perc_retweet_alltweets(all_tweets)
        f8=avg_urls_signal(signal_tweets)
        f9=avg_urls_all(all_tweets)
        f10=avg_hashtags_signal_tweet(signal_tweets)
        f11=avg_hahstags_all_tweets(all_tweets)
        f12=avg_usernames_signal_tweet(signal_tweets)
        f13=avg_usernames_all_tweets(all_tweets)
        return [f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13]

def gen_stream():
    """Generates stream of tweets"""
    with gzip.open('tweets.json.gz') as f:
        for line in f:
            try:
                yield json.loads(line.decode('utf-8'))
            except:
                continue


def pipeline():
    """real-time rumor detection pipeline"""
    for tweet in gen_stream():
        tweet_id=tweet['id']
        tweet_text=tweet['text'].translate(non_bmp_map)
        true_value=is_signal_tweet(tweet_text)
        if true_value==True:
            signal_tweets.append(tweet)
            signal_id_text.update({tweet_id:tweet_text})
            minhash(tweet_text,tweet_id,signal_minhashes,lsh_signal)
        else:
            non_signal_tweets.append(tweet)
            non_signal_id_text.update({tweet_id:tweet_text})
            minhash(tweet_text,tweet_id,non_signal_minhashes,lsh_non_signal)
    for key,value in signal_minhashes.items():  
        graph=generate_undirected_graph(key,value)
    conn_comp=connected_components(graph)
    for each_cluster in conn_comp:
        sig_tweets=[]
        for each_id in each_cluster:
            for k,v in signal_id_text.items():
                if each_id==k:
                    sig_tweets.append(v)
                    
        non_sig_tweets=[]
        sent=extract_summary(sig_tweets)
        sim_non_sig_tweets=non_signal_tweets_to_cluster(sent)
        for each in sim_non_signal_tweets:
            for k,v in non_signal_id_text:
                if each==k:
                    non_sig_tweets.append(v)
                    
        tot_tweets=sig_tweets+non_sig_tweets
        features=gen_statistical_features(tot_tweets,sig_tweets)
        #each|=set(sim_non_signal_tweets)
        
    
    

if __name__ == '__main__':
    pipeline()
