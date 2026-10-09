#!/usr/bin/env python3
"""Refresh an organizer-published public leaderboard snapshot, never a receipt.

Runs on an unrestricted GitHub Actions runner. Sandbox failures retain the last
successful snapshot and record a separate failed-attempt status. A cached score
is never presented as current without its check time. No authentication or
submission endpoint is used; zero weekly slots are spent.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
URL='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('td','th') and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row);self.row=None;self.cell=None


def parse_leaderboard(html):
    parser=TableRows();parser.feed(html)
    results=[]
    for cells in parser.rows:
        if not cells or not re.fullmatch(r'#?\d+',cells[0]):continue
        scores=[c for c in cells[1:] if re.fullmatch(r'(?:0|1)\.\d{4,}',c)]
        if len(scores)!=1:continue
        score=float(scores[0])
        if not 0<=score<=1:raise ValueError('organizer page score outside [0,1]')
        rank=int(cells[0].lstrip('#'))
        participant=cells[2] if len(cells)>=4 else cells[1]
        results.append(dict(rank=rank,participant_display=participant,public_dti=score))
    if not results or results[0]['rank']!=1:
        raise ValueError('no valid public leaderboard table; refusing to invent a feed')
    if any(a['public_dti']<b['public_dti'] for a,b in zip(results,results[1:])):
        raise ValueError('leaderboard not sorted; parser or page has changed')
    return results


def refresh(root=ROOT):
    evidence=root/'evidence';evidence.mkdir(exist_ok=True)
    now=datetime.now(timezone.utc).isoformat()
    status=dict(attempted_utc=now,url=URL)
    try:
        request=Request(URL,headers={'User-Agent':'57GEMSDOE-public-source-audit/1.0'})
        with urlopen(request,timeout=30) as response:
            final_url=response.url
            if '/login' in final_url:raise ValueError('public board redirected to login')
            html=response.read(4*1024*1024).decode('utf-8')
        rows=parse_leaderboard(html)
        snapshot=dict(evidence_class='ORGANIZER-PUBLISHED public leaderboard, NOT a submission-page receipt',
            source_url=URL,retrieved_utc=now,rows=rows,top_public_dti=rows[0]['public_dti'],
            organizer_confirmed_submission_score=None,private_score=None,
            weekly_slots_remaining=None,receipt_attribution_available=False)
        (evidence/'leaderboard_snapshot.json').write_text(json.dumps(snapshot,indent=2,allow_nan=False)+'\n')
        status.update(ok=True,rows=len(rows))
    except Exception as error:
        status.update(ok=False,error=str(error),retained_previous_snapshot=(evidence/'leaderboard_snapshot.json').exists())
    (evidence/'feed_refresh_status.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    return status


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    status=refresh();print(json.dumps(status,indent=2))
    # A failed source refresh is visible, not permission to discard the audited site.
    return 0


if __name__=='__main__':
    raise SystemExit(main())
