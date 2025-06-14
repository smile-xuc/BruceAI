# BruceAI

This repository contains a simple example client for the Alibaba Cloud realtime multimodal dialog service.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Example usage

Update `multimodal_client.py` with your `workspace_id`, `app_id` and `api_key`. Then run:

```bash
python multimodal_client.py
```

The script demonstrates how to create a `MultiModalDialog` session and connect via WebSocket using the interface defined in the Alibaba Cloud documentation.
