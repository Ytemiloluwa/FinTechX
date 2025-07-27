import logging
import uuid
import csv
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import threading
import time


class BatchStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    PARTIALLY_COMPLETED = "Partially Completed"


class BatchType(Enum):
    PAYMENT = "Payment"
    REFUND = "Refund"
    TRANSFER = "Transfer"
    CARD_ISSUANCE = "Card Issuance"
    CUSTOMER_IMPORT = "Customer Import"
    MERCHANT_IMPORT = "Merchant Import"


class BatchItem:
    def __init__(self, data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.data = data
        self.status = "Pending"
        self.error_message = None
        self.processed_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "data": self.data,
            "status": self.status,
            "error_message": self.error_message,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchItem':
        item = cls(data["data"])
        item.id = data["id"]
        item.status = data["status"]
        item.error_message = data["error_message"]

        if data.get("processed_at"):
            item.processed_at = datetime.fromisoformat(data["processed_at"])

        return item


class BatchJob:
    def __init__(
            self,
            name: str,
            batch_type: BatchType,
            items: List[BatchItem],
            description: str = "",
            metadata: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.batch_type = batch_type
        self.items = items
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.started_at = None
        self.completed_at = None
        self.status = BatchStatus.PENDING
        self.total_items = len(items)
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "batch_type": self.batch_type.value,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "items": [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchJob':
        batch_type = BatchType(data["batch_type"])
        items = [BatchItem.from_dict(item) for item in data["items"]]

        job = cls(
            name=data["name"],
            batch_type=batch_type,
            items=items,
            description=data["description"],
            metadata=data["metadata"]
        )

        job.id = data["id"]
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])

        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])

        job.status = BatchStatus(data["status"])
        job.total_items = data["total_items"]
        job.processed_items = data["processed_items"]
        job.successful_items = data["successful_items"]
        job.failed_items = data["failed_items"]

        return job

    def get_progress(self) -> float:
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100.0


class BatchProcessor:
    def __init__(self, process_function=None):
        self.process_function = process_function
        self.logger = logging.getLogger("fintechx_desktop.app.batch_processing")
        self.active_jobs = {}
        self.job_threads = {}

    def register_processor(self, batch_type: BatchType, processor_function):
        self.process_function = processor_function

    def process_batch(self, batch_job: BatchJob) -> None:
        if not self.process_function:
            self.logger.error(f"No processor function registered for batch type: {batch_job.batch_type.value}")
            batch_job.status = BatchStatus.FAILED
            batch_job.updated_at = datetime.now()
            return

        batch_job.status = BatchStatus.PROCESSING
        batch_job.started_at = datetime.now()
        batch_job.updated_at = datetime.now()

        for item in batch_job.items:
            try:
                result = self.process_function(item.data, batch_job.batch_type)

                if result.get("success", False):
                    item.status = "Completed"
                    batch_job.successful_items += 1
                else:
                    item.status = "Failed"
                    item.error_message = result.get("error", "Unknown error")
                    batch_job.failed_items += 1

            except Exception as e:
                self.logger.error(f"Error processing batch item {item.id}: {str(e)}")
                item.status = "Failed"
                item.error_message = str(e)
                batch_job.failed_items += 1

            item.processed_at = datetime.now()
            batch_job.processed_items += 1
            batch_job.updated_at = datetime.now()

        if batch_job.failed_items == 0:
            batch_job.status = BatchStatus.COMPLETED
        elif batch_job.successful_items == 0:
            batch_job.status = BatchStatus.FAILED
        else:
            batch_job.status = BatchStatus.PARTIALLY_COMPLETED

        batch_job.completed_at = datetime.now()
        batch_job.updated_at = datetime.now()

    def start_batch_job(self, batch_job: BatchJob) -> None:
        self.active_jobs[batch_job.id] = batch_job

        thread = threading.Thread(
            target=self._process_batch_thread,
            args=(batch_job,),
            daemon=True
        )

        self.job_threads[batch_job.id] = thread
        thread.start()

    def _process_batch_thread(self, batch_job: BatchJob) -> None:
        try:
            self.process_batch(batch_job)
        except Exception as e:
            self.logger.error(f"Error in batch processing thread for job {batch_job.id}: {str(e)}")
            batch_job.status = BatchStatus.FAILED
            batch_job.updated_at = datetime.now()

        # Clean up
        if batch_job.id in self.job_threads:
            del self.job_threads[batch_job.id]

    def get_batch_job(self, job_id: str) -> Optional[BatchJob]:
        return self.active_jobs.get(job_id)

    def get_all_batch_jobs(self) -> List[BatchJob]:
        return list(self.active_jobs.values())

    def get_batch_jobs_by_status(self, status: BatchStatus) -> List[BatchJob]:
        return [job for job in self.active_jobs.values() if job.status == status]

    def get_batch_jobs_by_type(self, batch_type: BatchType) -> List[BatchJob]:
        return [job for job in self.active_jobs.values() if job.batch_type == batch_type]


class BatchManager:
    def __init__(self):
        self.logger = logging.getLogger("fintechx_desktop.app.batch_processing")
        self.batch_jobs = {}
        self.processors = {}

        # Register default processors
        self._register_default_processors()

    def _register_default_processors(self):
        self.register_processor(BatchType.PAYMENT, self._process_payment)
        self.register_processor(BatchType.REFUND, self._process_refund)
        self.register_processor(BatchType.TRANSFER, self._process_transfer)
        self.register_processor(BatchType.CARD_ISSUANCE, self._process_card_issuance)
        self.register_processor(BatchType.CUSTOMER_IMPORT, self._process_customer_import)
        self.register_processor(BatchType.MERCHANT_IMPORT, self._process_merchant_import)

    def register_processor(self, batch_type: BatchType, processor_function):
        processor = BatchProcessor(processor_function)
        self.processors[batch_type] = processor

    def create_batch_job(
            self,
            name: str,
            batch_type: BatchType,
            items: List[Dict[str, Any]],
            description: str = "",
            metadata: Dict[str, Any] = None
    ) -> str:
        batch_items = [BatchItem(item) for item in items]

        batch_job = BatchJob(
            name=name,
            batch_type=batch_type,
            items=batch_items,
            description=description,
            metadata=metadata or {}
        )

        self.batch_jobs[batch_job.id] = batch_job
        self.logger.info(f"Created batch job {batch_job.id}: {name} ({batch_type.value})")

        return batch_job.id

    def start_batch_job(self, job_id: str) -> bool:
        batch_job = self.get_batch_job(job_id)
        if not batch_job:
            self.logger.warning(f"Attempted to start non-existent batch job: {job_id}")
            return False

        if batch_job.status != BatchStatus.PENDING:
            self.logger.warning(f"Attempted to start batch job {job_id} with status {batch_job.status.value}")
            return False

        processor = self.processors.get(batch_job.batch_type)
        if not processor:
            self.logger.error(f"No processor registered for batch type: {batch_job.batch_type.value}")
            batch_job.status = BatchStatus.FAILED
            batch_job.updated_at = datetime.now()
            return False

        processor.start_batch_job(batch_job)
        self.logger.info(f"Started batch job {job_id}")

        return True

    def get_batch_job(self, job_id: str) -> Optional[BatchJob]:
        return self.batch_jobs.get(job_id)

    def get_all_batch_jobs(self) -> List[BatchJob]:
        return list(self.batch_jobs.values())

    def get_batch_jobs_by_status(self, status: BatchStatus) -> List[BatchJob]:
        return [job for job in self.batch_jobs.values() if job.status == status]

    def get_batch_jobs_by_type(self, batch_type: BatchType) -> List[BatchJob]:
        return [job for job in self.batch_jobs.values() if job.batch_type == batch_type]

    def delete_batch_job(self, job_id: str) -> bool:
        if job_id in self.batch_jobs:
            batch_job = self.batch_jobs[job_id]

            if batch_job.status == BatchStatus.PROCESSING:
                self.logger.warning(f"Attempted to delete batch job {job_id} that is currently processing")
                return False

            del self.batch_jobs[job_id]
            self.logger.info(f"Deleted batch job {job_id}")
            return True

        self.logger.warning(f"Attempted to delete non-existent batch job: {job_id}")
        return False

    def export_batch_job_results(self, job_id: str, file_path: str, format: str = "csv") -> bool:
        batch_job = self.get_batch_job(job_id)
        if not batch_job:
            self.logger.warning(f"Attempted to export non-existent batch job: {job_id}")
            return False

        try:
            if format.lower() == "csv":
                return self._export_to_csv(batch_job, file_path)
            elif format.lower() == "json":
                return self._export_to_json(batch_job, file_path)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False

        except Exception as e:
            self.logger.error(f"Error exporting batch job {job_id}: {str(e)}")
            return False

    def _export_to_csv(self, batch_job: BatchJob, file_path: str) -> bool:
        try:
            with open(file_path, 'w', newline='') as csvfile:
                # Determine headers from the first item's data keys
                headers = ["id", "status", "error_message", "processed_at"]

                if batch_job.items:
                    data_keys = batch_job.items[0].data.keys()
                    for key in data_keys:
                        headers.append(f"data_{key}")

                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()

                for item in batch_job.items:
                    row = {
                        "id": item.id,
                        "status": item.status,
                        "error_message": item.error_message or "",
                        "processed_at": item.processed_at.isoformat() if item.processed_at else ""
                    }

                    # Add data fields with "data_" prefix
                    for key, value in item.data.items():
                        row[f"data_{key}"] = value

                    writer.writerow(row)

            return True

        except Exception as e:
            self.logger.error(f"Error exporting batch job to CSV: {str(e)}")
            return False

    def _export_to_json(self, batch_job: BatchJob, file_path: str) -> bool:
        try:
            with open(file_path, 'w') as jsonfile:
                json.dump(batch_job.to_dict(), jsonfile, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Error exporting batch job to JSON: {str(e)}")
            return False

    def import_batch_from_csv(
            self,
            file_path: str,
            batch_type: BatchType,
            name: str = None,
            description: str = "",
            metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        try:
            items = []

            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    item_data = {}

                    # Extract data fields (those without special prefixes)
                    for key, value in row.items():
                        if not key.startswith("id") and not key.startswith("status") and not key.startswith(
                                "error") and not key.startswith("processed"):
                            item_data[key] = value

                    items.append(item_data)

            if not name:
                name = f"Imported {batch_type.value} Batch - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return self.create_batch_job(
                name=name,
                batch_type=batch_type,
                items=items,
                description=description,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Error importing batch from CSV: {str(e)}")
            return None

    def _process_payment(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate payment processing
            time.sleep(0.1)  # Simulate processing time

            # Validate required fields
            required_fields = ["amount", "card_number", "expiry", "cvv"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # Simulate success/failure based on amount
            amount = float(data.get("amount", 0))
            if amount <= 0:
                return {"success": False, "error": "Invalid amount"}

            # 90% success rate for demo purposes
            if hash(data.get("card_number", "")) % 10 != 0:
                return {"success": True, "transaction_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Payment declined"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_refund(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate refund processing
            time.sleep(0.1)  # Simulate processing time

            # Validate required fields
            required_fields = ["transaction_id", "amount"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 95% success rate for demo purposes
            if hash(data.get("transaction_id", "")) % 20 != 0:
                return {"success": True, "refund_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Refund failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_transfer(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate transfer processing
            time.sleep(0.1)  # Simulate processing time

            # Validate required fields
            required_fields = ["source_account", "destination_account", "amount"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 92% success rate for demo purposes
            if hash(data.get("source_account", "")) % 12 != 0:
                return {"success": True, "transfer_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Transfer failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_card_issuance(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate card issuance processing
            time.sleep(0.2)  # Simulate processing time

            # Validate required fields
            required_fields = ["customer_id", "card_type"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 98% success rate for demo purposes
            if hash(data.get("customer_id", "")) % 50 != 0:
                return {
                    "success": True,
                    "card_id": str(uuid.uuid4()),
                    "card_number": f"4{''.join([str(hash(data.get('customer_id', '')))[i % 5] for i in range(15)])}"
                }
            else:
                return {"success": False, "error": "Card issuance failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_customer_import(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate customer import processing
            time.sleep(0.1)  # Simulate processing time

            # Validate required fields
            required_fields = ["first_name", "last_name", "email"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 96% success rate for demo purposes
            if hash(data.get("email", "")) % 25 != 0:
                return {"success": True, "customer_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Customer import failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_merchant_import(self, data: Dict[str, Any], batch_type: BatchType) -> Dict[str, Any]:
        try:
            # Simulate merchant import processing
            time.sleep(0.15)  # Simulate processing time

            # Validate required fields
            required_fields = ["name", "category", "contact_email"]
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 94% success rate for demo purposes
            if hash(data.get("name", "")) % 16 != 0:
                return {"success": True, "merchant_id": str(uuid.uuid4())}
            else:
                return {"success": False, "error": "Merchant import failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}
