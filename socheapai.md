2.1 Prepare
Prepare the following first:

BASE_URL
A valid Media API Key
A publicly accessible reference image URL, if you want to use reference/image generation
We recommend passing the API Key in the request header:

```
export BASE_URL="https://socheap.ai"
export API_KEY="your-media-api-key"

```

2.2 Read Catalog
We recommend reading the catalog first, then choosing the appropriate model, mode, resolution, aspect_ratio, and generation_type.

Video catalog:

```
curl "$BASE_URL/media/catalog" \
 -H "Authorization: Bearer $API_KEY"
```

Video catalog model entries include supports_extend=true and extend_modes when a model can create extendable sources and extend_video jobs. can_extend is a generation response field, not a catalog capability field.
When a model has different defaults by generation type, the catalog may include constraints.defaults_by_generation_type. For example, grok-imagine-video uses top-level/text-to-video aspect_ratio=2:3, but reference_to_video defaults to 16:9.

Image catalog:

```
curl "$BASE_URL/media/image/catalog" \
 -H "Authorization: Bearer $API_KEY"
```

2.4 Create An Image Job

```
curl -X POST "$BASE_URL/media/image/generations" \
 -H "Authorization: Bearer $API_KEY" \
 -H "Content-Type: application/json" \
 -d '{
"model": "nano-banana-pro",
"client_request_id": "quickstart-image-001",
"prompt": "Turn this into a crisp ecommerce hero image",
"image_urls": ["<https://example.com/ref.png>"],
"resolution": "4K",
"aspect_ratio": "9:16"
}'
```

2.5 Poll Job Status
After the create endpoint returns, save the id from the response and poll:
Image:

```
curl "$BASE_URL/media/image/generations/<id>" \
  -H "Authorization: Bearer $API_KEY"
```

2.7 Common Flow
The most common request flow is:

1. POST /media/generations or POST /media/image/generations
2. Save the returned id
3. Poll GET /media/.../:id
4. After the job completes, read the output URL from result

5.3 gpt-image-2

```
curl -X POST "$BASE_URL/media/image/generations" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "client_request_id": "image-demo-003",
    "prompt": "A simple red ceramic mug on a clean white studio background",
    "resolution": "1K",
    "aspect_ratio": "auto"
  }'
```

Completed response example:

```
{
    "code": 0,
    "message": "success",
    "data": {
        "id": "77777777-7777-7777-7777-777777777777",
        "client_request_id": "image-demo-003",
        "kind": "image",
        "status": "completed",
        "model": "gpt-image-2",
        "mode": "standard",
        "family": "gpt-image",
        "can_cancel": false,
        "prompt": "A simple red ceramic mug on a clean white studio background",
        "image_urls": [],
        "resolution": "1K",
        "aspect_ratio": "auto",
        "estimated_base_cost": 0.22,
        "estimated_cost": 0.033,
        "actual_base_cost": 0.22,
        "actual_cost": 0.033,
        "rate_multiplier": 0.15,
        "result": {
            "outputs": ["<generated-image-url>"]
        },
        "created_at": "Sat, 11 Apr 2026 08:33:05 GMT",
        "submitted_at": "Sat, 11 Apr 2026 08:33:07 GMT",
        "completed_at": "Sat, 11 Apr 2026 08:33:24 GMT",
        "poll_url": "/media/image/generations/77777777-7777-7777-7777-777777777777",
        "cancel_url": "/media/image/generations/77777777-7777-7777-7777-777777777777/cancel"
    }
}
```
