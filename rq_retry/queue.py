from datetime import datetime
from rq.queue import Queue


class DeadLetterQueue(Queue):
    """Queue of permanently failed jobs

    The DeadLetterQueue holds messages that originally came from other queues.
    It is similar to the FailedQueue. Functionally the difference is that
    DeadLetterQueue.quarantine() moves a message from a source queue whereas
    FailedQueue.quarantine() adds a message to the failed queue.

    The DeadLetterQueue can be used by retry logic: after retying a job
    some number of times the job can be moved from the FailedQueue to the
    DeadLetterQueue. (This could potentially be extended to multiple levels
    of dead letter queues.
    """
    def __init__(self, name, connection):
        super(DeadLetterQueue, self).__init__(name=name, connection=connection)

    def quarantine(self, job, queue):
        """Moves job from the specified queue to the dead letter queue"""
        with self.connection._pipeline() as pipeline:
            self.connection.sadd(self.redis_queues_keys, self.key)
            job.ended_at = datetime.utcnow()
            job.save(pipeline=pipeline)
            self.push_job_id(job.id, pipeline=pipeline)
            queue.remove(job.id, pipeline=pipeline)
            pipeline.execute()
        return job
